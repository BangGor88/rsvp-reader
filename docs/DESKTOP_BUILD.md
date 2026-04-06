# Desktop Build and Release

## Build executable

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_exe.ps1
```

Produces:

- `dist\RSVPReader.exe`

## Create release artifact

```powershell
powershell -ExecutionPolicy Bypass -File scripts\release_exe.ps1
```

Creates:

- `release\RSVPReader-<timestamp>\<version>.exe`
- `release\RSVPReader-<timestamp>\<version>.sha256.txt`
- `release\RSVPReader-<timestamp>\RELEASE_NOTES.txt`