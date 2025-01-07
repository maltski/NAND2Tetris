import os
import platform

windows = platform.system() == 'Windows'
executable = 'python' if windows else 'python3'
scriptExt = 'bat' if windows else 'sh'

def main(entrypoint = 'JackCompiler.py'):
    """
    Calls JackCompiler.py with each folder in the project directory and
    expects that a .vm file is produced.
    """

    test_vm_dir = os.path.join('..', '11', 'test_vm_files')
    folders = [entry for entry in os.listdir() if os.path.isdir(entry) and 'pycache' not in entry]
    results = []
    cmd = os.path.join('..', '..', 'tools', f'TextComparer.{scriptExt}')

    for folder in folders:
        print('*' * 80)
        print(f'Testing folder {folder}')
        code = os.system(f'{executable} {entrypoint} {folder}')
        if code != 0:
            print(f'Compiler failed on {folder}')

        names = [entry.replace('.jack', '') for entry in os.listdir(folder) if entry.endswith('.jack')]
        for name in names:
            file = f'{folder}\{name}.vm'
            test_file = f'{folder}_{name}.vm'
            if not os.path.exists(file):
                print(f'Missing compiled output for {file}')

            filesRef = os.path.join(test_vm_dir, test_file)

            print(f'Comparing {file} with {filesRef}')
            code = os.system(f'{"" if windows else "sh "}{cmd} {file} {filesRef}')
            results.append((filesRef, code))

    print('\n' + '=' * 36 + 'SUMMARY' + '=' * 37 + '\n')

    passed = 0
    for program, result in results:
        print(f'{program:<40}: ', end="")
        if result == 0:
            print("passed")
            passed += 1
        else:
            print("failed")

    print(f'\nPassed {passed} of {len(results)}')

if __name__ == "__main__":
    main()