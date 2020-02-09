#
#  Copyright 2001 - 2016 Ludek Smid [http://www.ospace.net/]
#
#  This file is part of Pygame.UI.
#
#  Pygame.UI is free software; you can redistribute it and/or modify
#  it under the terms of the Lesser GNU General Public License as published by
#  the Free Software Foundation; either version 2.1 of the License, or
#  (at your option) any later version.
#
#  Pygame.UI is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  Lesser GNU General Public License for more details.
#
#  You should have received a copy of the Lesser GNU General Public License
#  along with Pygame.UI; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

delimiters = [" ", ".", "-", "(", ")", "{", "}", "[", "]", ",", ":",\
              ";", "/", "\\", "\"", "<", ">", "?", "!", "+", "*", "&",\
              "^", "@", "#", "$", "%", "^", "=", "|", "~"]

def splitter(text, delims = None):
    """Splits given string into parts separated by more delimiters.

    delims parameter is list of delimiter characters. Function returns
    tuple containg word, starting postion of word and ending position
    of word. Given word can be taken from text as text[start:end].
    Example:
        text = "This is line"
        result = ""
        for word in splitter(text, [" "]):
            result = result + text[word[1]:word[2]] + " "
        print result
        result = ""
        for word in splitter(text, [" "]):
            result = result + word[0] + " "
        print result
    """
    #stores result
    result = []
    #if delimiter is not specified, use defaults
    if delims == None:
        delims = delimiters
    #starting with empty word
    word = ""
    #starting position of word
    start = 0
    #traverse string by chars
    for i in range(len(text)):
        #test, if char is delimiter
        if text[i] in delims:
            #is delimiter, so add new word (non empty) to result
            if len(word) > 0:
                result.append((word, start, i))
            #start new word
            word = ""
            #skip delimiter
            start = i + 1
        else:
            #char is not delimiter, so append it to word
            word = word + text[i]

    #append last word to result
    if len(word) > 0:
        #handle end of text with no delimiter
        if start + len(word) == len(text):
            #word end beyond end of text
            i = i + 1
        result.append((word, start, i))

    return result
