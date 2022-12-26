import os
import subprocess
import zipfile

print("Getting git ignored files")
files = subprocess.run(
    ['git', 'ls-files'],
    stdout=subprocess.PIPE
).stdout.decode().splitlines()
basename = os.path.basename(os.getcwd())
zip_file = zipfile.ZipFile(f"{basename}.zip", 'w')

print("Zipping files...\n")
for filename in files:
    print(f"Zipping {filename}")
    zip_file.write(filename, filename)

print("\nDone zipping!")
zip_file.close()
