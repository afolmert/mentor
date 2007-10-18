" Vim syntax file
" This is syntax file for Mentor Probe markup language
" Language:	Mentor Probe source file
" Maintainer:	Adam Folmert <afolmert@gmail.com)
" Last Change:	Fr, 04 Nov 2005 12:46:45 CET

" Quit when a syntax file was already loaded
if exists("b:current_syntax")
  finish
endif


"
" PrbComment: either beginning of line or any char not backspace \
syn match PrbComment /\(^\|[^\\]\)%.*/ containedin=ALL
syn match PrbCommand /\\tabbed\|\\title\|\\section\|\\subsection\\|\\set\|\\cloze/
syn match PrbCloze  /[a-zA-Z0-9-]*_[a-zA-Z0-9-]*/

" PrbRange is a virtual region which contains all other regions
" It was created to avoid false highlighting of items outside probe command
syn region PrbRange start=+\\tabbed\|\\title\|\\section\|\\subsection\\|\\set\|\\cloze+ end=+}+ contains=PrbCommand,PrbOption,PrbGroup,PrbHint keepend
syn region PrbOption start=+\[+ end=+\]+
syn region PrbGroup start=+{+ end=+}+ contains=PrbCloze,PrbHint
syn match PrbHint /#{[^{}]*}/


" hi def link PrbContent   Comment
hi def link PrbComment   Comment
hi def link PrbGroup     Normal
hi def link PrbOption    Keyword
hi def link PrbCommand   Keyword
hi def link PrbCloze     Typedef
hi def link PrbHint      String
hi def link PrbRange     Error



let b:current_syntax = "probe"


