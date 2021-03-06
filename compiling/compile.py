#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

# This builds index.html by compressing, wrapping, and syntax-highlighting parts/intro.js and parts/uncompressed.js
# HTML tags can be added to those files using 〈,〉 instead of <,>

import sys
import os
import httplib, urllib
import subprocess
import re
import codecs
from pprint import pprint

SCREEN_WIDTH = 200
FUNC_DELIMITER = ";5;"

# Move to the project root directory by getting the current script's path and moving to its parent
os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])));
os.chdir("..");

print "Getting component Parts..."

# Open the introductory comments file
f = codecs.open("parts/intro.js","r","utf-8")
intro = f.read()
f.close()

# Open the statements file
f = codecs.open("parts/statements.js","r","utf-8")
statements = f.read()
f.close()

# Open the uncompressed file
f = codecs.open("parts/control.js","r","utf-8")
control = f.read()
f.close()

# Make the statements into a function, delimited by FUNC_DELIMITER, so that is looks better
print "Creating statement function..."
#pprint(re.findall("//.*\n",statements))
statements = re.sub("//.*\n","",statements,re.M|re.S)
function = "function l() {" +re.sub("\n+",FUNC_DELIMITER,statements,re.M|re.S) + "}"

# Compress the code using Google's Closure Compiler with RESTful API (this is taken from https://developers.google.com/closure/compiler/docs/api-tutorial1)
print "Compressing using the closure compiler..."
params = urllib.urlencode([
	("js_code", control.encode("utf-8")),
	("compilation_level", "WHITESPACE_ONLY"),
	("output_format", "text"),
	("output_info", "compiled_code"),
])
headers = { "Content-type": "application/x-www-form-urlencoded" }
c = httplib.HTTPConnection("closure-compiler.appspot.com")
c.request("POST", "/compile", params, headers)
response = c.getresponse()
compressed = response.read()
c.close()

# Add the introductory text at the start
combined = intro + function + compressed

# Remove any newlines
combined = combined.replace("\n","")

# Wrap the text, ignoring 〈tags〉
print "Wrapping text..."
combined = combined
wrapped = ""
pos = 0
inTag = False
for i in combined:
	wrapped += i
	if i == u"\u2329": inTag = True
	if i == u"\u232A": 
		inTag = False
	elif not inTag: # Sneaky
		pos = (pos + 1) % SCREEN_WIDTH
		if pos == 0: wrapped += "\n"

# Highlight the text
print "Highlighting syntax..."
escaped = wrapped.replace("\\","\\\\").replace("\"","\\\"").replace("\n","\\n")
highlighted = subprocess.check_output(["nodejs","-e","h=require(\"highlight.js\");console.log(h.highlight(\"javascript\",\""+escaped+"\",true).value)"])

# Replace 〈,〉 with <,>
highlighted = highlighted.decode("utf-8").replace(u"\u2329",u"<").replace(u"\u232A",u">")

# Escape backslashes for the regex engine
highlighted = highlighted.replace("\\","\\\\")

# Put the highlighted code in the HTML file
print "Saving to the HTML file..."
f = codecs.open("index.html","r+","utf-8")
html = f.read()
new_html = re.sub("<pre id=\"n\">.*</pre>",'<pre id="n">'+highlighted+'</pre>',html,flags=re.S|re.M)
f.seek(0)
f.write(new_html)
f.truncate()
f.close()

print "Done."
