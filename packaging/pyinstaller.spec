# -*- mode: python ; coding: utf-8 -*-
#
# Copyright © 2012-2026 Ejwa Hosting AB. All rights reserved.
#
# This file is part of gitinspector.
#
# gitinspector is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# gitinspector is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with gitinspector. If not, see <http://www.gnu.org/licenses/>.
#
# One executable carrying the interpreter, the html templates and the compiled translations, for
# the people who want to run gitinspector without installing Python. Build it with
#
#   pyinstaller --clean --noconfirm packaging/pyinstaller.spec
#
# basedir.get_basedir() answers with the directory the bundle is unpacked into, so the data below
# has to keep the names it has in the package.

import glob
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(SPEC)))
TRANSLATIONS = [(catalog, "translations")
                for catalog in glob.glob(os.path.join(ROOT, "gitinspector", "translations", "*.mo"))]

analysis = Analysis([os.path.join(ROOT, "gitinspector.py")],
                    pathex=[ROOT],
                    datas=[(os.path.join(ROOT, "gitinspector", "html"), "html")] + TRANSLATIONS,
                    excludes=["tkinter", "unittest"],
                    noarchive=False)

archive = PYZ(analysis.pure)

executable = EXE(archive, analysis.scripts, analysis.binaries, analysis.datas, [],
                 name="gitinspector",
                 console=True,
                 strip=False,
                 upx=False)
