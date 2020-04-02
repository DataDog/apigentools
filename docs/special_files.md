# Special Files

Apigentools supports special files in the generated clients that modify the behavior of the generation process

## .generated_files
This file can be placed at the root of any generated client folder. Each line contains a regex to a file and path of each generated file. 
Ex:

```
docs/*
api\/.*(?<!_test.*)$
```

This tells apigentools that the all files in the `docs` folder, and all files in the `api` folder that **don't** end
in `_test.` are generated files. Passing the `--delete-generated-files` flag into `apigentools generate` will 
cause any files matching these regexes to be deleted prior to the next generation.

This ensures that the generated files always winds up in a clean state between generations, while leaving behind any manually 
written code, such as tests, utility methods, CI files, etc.