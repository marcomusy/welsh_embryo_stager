# -*- mode: python ; coding: utf-8 -*-
# https://discourse.vtk.org/t/python-vtk-and-pyinstaller/418/4
#
# rm build dist __pycache__
# pyinstaller stager.spec

from vedo import installdir as vedo_installdir
import os
vedo_installdir = os.path.join(vedo_installdir,'fonts')
print(vedo_installdir)


block_cipher = None


added_files = [
    ('tuning/*', 'tuning/'), ##doesnt work?
    #('../vedo/vedo/fonts/*', 'vedo/fonts/'), ##OK
    (vedo_installdir+'/*', 'vedo/fonts/'), ##OK
]

a = Analysis(['stager.py'],
             pathex=[],
             binaries=[],
             hiddenimports=[
                 'vtkmodules',
                 'vtkmodules.all',
                 'vtkmodules.util',
                 'vtkmodules.util.numpy_support',
             ],
             datas = added_files,
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

#splash = Splash('a.jpg',
#                binaries=a.binaries,
#                datas=a.datas,
#                text_pos=None,
#                text_size=12,
#                minify_script=True)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
 #         splash,
 #         splash.binaries,
          [],
          name='stager',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )
