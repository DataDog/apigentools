# Unless explicitly stated otherwise all files in this repository are licensed
# under the 3-clause BSD style license (see LICENSE).
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2019 Datadog, Inc.
import glob
import logging
import os
import shutil
import subprocess
import tempfile

from apigentools.commands.command import Command
from apigentools.constants import OPENAPI_GENERATOR_GIT
from apigentools.utils import run_command

log = logging.getLogger(__name__)


class TemplatesCommand(Command):
    def run(self):
        with tempfile.TemporaryDirectory() as td:
            log.info("Obtaining upstream templates ...")
            patch_in = copy_from = td
            if self.args.templates_source == "openapi-jar":
                run_command(["unzip", "-q", self.args.jar_path, "-d", td])
            elif self.args.templates_source == "local-dir":
                for lang in self.config.languages:
                    lang_upstream_templates_dir = self.config.get_language_config(lang).upstream_templates_dir
                    local_lang_dir = os.path.join(self.args.local_path, lang_upstream_templates_dir)
                    if not os.path.exists(local_lang_dir):
                        log.error(
                            "Directory %s doesn't contain '%s' directory with templates. " +
                            "Make sure %s contains directories with templates for all languages",
                            self.args.local_path, lang_upstream_templates_dir, self.args.local_path
                        )
                        return 1
                    shutil.copytree(local_lang_dir, os.path.join(td, lang))
            else:
                patch_in = copy_from = os.path.join(
                    td, "modules", "openapi-generator", "src", "main", "resources"
                )
                run_command(["git", "clone", OPENAPI_GENERATOR_GIT, td])
                run_command(["git", "-C", td, "checkout", self.args.git_committish])

            if os.path.exists(self.args.template_patches_dir):
                log.info("Applying patches to upstream templates ...")
                patches = glob.glob(os.path.join(self.args.template_patches_dir, "*.patch"))
                for p in sorted(patches):
                    try:
                        run_command([
                            "patch",
                            "--no-backup-if-mismatch",
                            "-p1",
                            "-i",
                            os.path.abspath(os.path.join(self.args.template_patches_dir, os.path.basename(p))),
                            "-d",
                            patch_in,
                        ])
                    except subprocess.CalledProcessError:
                        # at this point, the stdout/stderr of the process have been printed by
                        # `run_command`, so the user should have sufficient info to about what went wrong
                        log.error(
                            "Failed to apply patch %s, exiting as templates can't be processed", p
                        )
                        return 1

            # copy the processed templates from the temporary dir to templates dir
            languages = self.args.languages or self.config.languages
            for lang in languages:
                upstream_templatedir = self.config.languages[lang].get("upstream_templates_dir", lang)
                outlang_dir = os.path.join(self.args.output_dir, lang)
                if os.path.exists(outlang_dir):
                    shutil.rmtree(outlang_dir)
                shutil.copytree(os.path.join(copy_from, upstream_templatedir), outlang_dir)
        return 0
