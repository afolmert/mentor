" Vim syntax file
" Language:	Mentor Probe markup language
" Maintainer:	Adam Folmert <afolmert@gmail.com>
" Last Change:	2007.10.19
" License:	GNU GPL, version 2.0 or later
" URL:		http://code.google.com/p/mentor/


" Quit when a syntax file was already loaded
if exists("b:current_syntax")
  finish
endif


" Define syntax groups
" PrbComment: either beginning of line or any char not backspaced \
syn match PrbComment /\(^\|[^\\]\)%.*/ containedin=ALL
syn match PrbCommand /\\title\|\\section\|\\subsection\|\\tabbed\|\\sentence\|\\paragraph\|\\definition\|\\subsubsection\|\\verbatim\|\\code\|\\pythoncode/
" this only if it starts after PrbCommand !
syn region PrbOption start=+\[+ end=+\]+
" this only if it starts after PrbCommand !
syn region PrbContent start=+{+ end=+}+ contains=PrbMarked,PrbIgnored
syn region PrbMarked start=+|+ end=+|+ contains=PrbHint,PrbMarkup keepend
syn region PrbIgnored start=+/+ end=+/+ contains=PrbMarkup keepend
syn match PrbHint /.\+\(?\|!\)/
" special markup which should be hidden so it does not clutter screen
syn match PrbMarkup /|\|\//  containedin=PrbMarked,PrbIgnored,PrbHint

" Define colors links
hi def link PrbComment   Comment
hi def link PrbContent   Normal
hi def link PrbOption    Keyword
hi def link PrbCommand   Keyword
hi def link PrbMarked    Normal
hi def link PrbIgnored   Normal
hi def link PrbHint      Comment
hi def link PrbMarkup    Comment


let b:current_syntax = "probe"


