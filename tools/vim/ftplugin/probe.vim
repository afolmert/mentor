" Vim filetype plugin file (GUI menu and keyboard operations)
" Language:	Mentor Probe markup language
" Maintainer:	Adam Folmert <afolmert@gmail.com>
" Last Change:	2007.10.19
" License:	GNU GPL, version 2.0 or later
" URL:		http://code.google.com/p/mentor/
"
"
" TODO
" gui menu for opetions
" shortcuts for wrapping with markup (ie, markup cloze)
" see SuperMemo incremental reading form and latex-suite for inspiration
"
"

" Only do this when not done yet for this buffer
if exists("b:did_ftplugin")
  finish
endif


" Don't load another plugin for this buffer
let b:did_ftplugin = 1


" automatically format text for textwidth 80
setlocal formatoptions=qta
set textwidth=80


" vim:sts=2:sw=2:

