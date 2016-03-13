/*
#
#  Copyright 2001 - 2006 Ludek Smid [http://www.ospace.net/]
#
#  This file is part of IGE - Outer Space.
#
#  IGE - Outer Space is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  IGE - Outer Space is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with IGE - Outer Space; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
*/

#ifdef __GNUG__
	#pragma implementation "Update.cpp"
#endif

// For compilers that support precompilation
#include "wx/wxprec.h"

#ifdef __BORLANDC__
	#pragma hdrstop
#endif

#include "Update.h"

#include "wx/progdlg.h"
#include "wx/textfile.h"
#include "wx/utils.h"

bool MakeDir(wxString &dirname) {
	OutputDebugString(wxString::Format("Creating directory %s.\n", dirname));
	wxString dstDirname = wxPathOnly(dirname);
	if (dstDirname == ".") {
		return 1;
	}
	if (!wxDirExists(dstDirname)) {
		MakeDir(dstDirname);
	}
	return wxMkdir(dirname);
}

bool CopyFile(wxString &srcDir, wxString &dstDir, wxString &filename) {
	wxString srcFile = wxString::Format("%s/%s", srcDir, filename);
	wxString dstFile = wxString::Format("%s/%s", dstDir, filename);
	wxString dstDirname = wxPathOnly(dstFile);
	// test if file exists
	if (!wxFileExists(srcFile)) {
		OutputDebugString(wxString::Format("%s does not exists.\n", srcFile));
		return 0;
	}
	// check if target directory exists
	if (!wxDirExists(dstDirname)) {
		if (!MakeDir(dstDirname)) {
			OutputDebugString(wxString::Format("Cannot create directory %s.\n", dstDirname));
			return 0;
		}
	}
	// check if target file exists
	if (wxFileExists(dstFile)) {
			wxRemoveFile(dstFile);
	}
	// all is ok -> copy it
	int retries = 30;
	while (retries > 0) {
		if (wxCopyFile(srcFile, dstFile, TRUE)) {
			break;
		}
		OutputDebugString("Copy failed - retrying\n");
		retries --;
		wxSleep(1);
	}
	return retries > 0;
}

bool RemoveFile(wxString &srcDir, wxString &dstDir, wxString &filename) {
	wxString dstFile = wxString::Format("%s/%s", dstDir, filename);
	if (wxDirExists(dstFile)) {
		OutputDebugString(wxString::Format("Removing dir %s.\n", dstFile));
		return wxRmdir(dstFile);
	}
	if (wxFileExists(dstFile)) {
		OutputDebugString(wxString::Format("Removing file %s.\n", dstFile));
		return wxRemoveFile(dstFile);
	}
	OutputDebugString(wxString::Format("Failed removing %s.\n", dstFile));
	return 0;
}

//------------------------------------------------------------------------------
// MyApp
//------------------------------------------------------------------------------

IMPLEMENT_APP(MyApp)

MyApp::MyApp()
{
}

bool MyApp::OnInit()
{
	// show dialog
	wxProgressDialog &dlg = wxProgressDialog("Outer Space Updater", "Initializing update...", 100);
	// load file with operations
	wxTextFile &operations = wxTextFile();
	if (!operations.Open(".update")) {
		// file does not exist
		return FALSE;
	}
	// init iterations over lines
	// load information from header
	wxString srcDir = operations.GetFirstLine();
	wxString targetDir = operations.GetNextLine();
	wxString executeApp = operations.GetNextLine();
	long maxOper;
	operations.GetNextLine().ToLong(&maxOper);
	// perform operations
	long counter = 0;
	wxString line, oper, filename;
	while (! operations.Eof()) {
		line = operations.GetNextLine();
		filename = line.Mid(1);
		OutputDebugString(wxString::Format("File: %s\n", filename));
		OutputDebugString(wxString::Format("Oper: %c\n", line.GetChar(0)));
		dlg.Update((counter * 100) / maxOper, wxString::Format("Updating file %s...", filename));
		switch (line.GetChar(0)) {
			case 'C':
				CopyFile(srcDir, targetDir, filename);
				break;
			case 'D':
				RemoveFile(srcDir, targetDir, filename);
				break;
			default:
				OutputDebugString("Bad operation\n")
				wxASSERT("Bad operation");
		}
		counter ++;
	}
	// execute execName
	wxExecute(executeApp, FALSE);
	dlg.Show(FALSE);
	return FALSE;
}
