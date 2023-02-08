# GitInfo
A PlatformIO pre-build script that commits all your changes on the active branch to a 'test_builds' branch and generates a header file you can include in your project that contains the SHA, commit date and branch

The script generates two files, GitInfo.cpp and GitInfo.h. by using
```cpp
#include <GitInfo.h>
```
you can have access to the SHA, commit date and branch but this file will show up as missing until the first time you build after adding this library. I can't include them in the git repository because tracking these files in git would cause a recursive issue.

_NOTE: You'll need to update the script with your project root directory. In the future, I'll break this out or find a way to auto-detect it_