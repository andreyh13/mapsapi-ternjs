#!/usr/bin/python

import urllib, json, libxml2dom, re

def collect_text(node):
    s = ""
    for child_node in node.childNodes:
        if child_node.nodeType == child_node.TEXT_NODE:
            s += child_node.nodeValue
        else:
            s += collect_text(child_node)
    return s

def processH2(node, data, classes, objects):
	#print "Processing H2"
	path = ''
	obj = ''
	obj_type = ''
	for child in node.childNodes:
		if child.tagName == 'span' and child.hasAttribute('itemprop') and child.getAttribute('itemprop') == 'path':
			path = collect_text(child)
		if child.tagName == 'span' and child.hasAttribute('itemprop') and child.getAttribute('itemprop') == 'name':
			obj = collect_text(child)
		if child.nodeType == child.TEXT_NODE:
			obj_type = child.nodeValue

	if path != '' and obj != '' and obj_type != '':
		arr_path = path.split('.')
		target = data
		for p in arr_path:
			if not p in target:
				target[p] = dict()
			target = target[p]
		arr_obj = obj.split('.')	
		if 'class' in obj_type:
			classes[obj] = path + '.' + obj
			for o in arr_obj:
				if not o in target:
					target[o] = dict()
				target = target[o]
			target["!url"] = docs_ref + "#" + node.getAttribute("id")
			target["prototype"] = dict()
			#target["!type"] = '?'	
		elif 'object' in obj_type:
			objects.append(obj)
			target = data['!define']
			for o in arr_obj:
				if not o in target:
					target[o] = dict()
				target = target[o]
			target["!url"] = docs_ref + "#" + node.getAttribute("id")
			#target["!type"] = 'Object'
		elif 'namespace' in obj_type:
			l_namespaces[obj] = path + '.' + obj
			for o in arr_obj:
				if not o in target:
					target[o] = dict()
				target = target[o]	
			target["!url"] = docs_ref + "#" + node.getAttribute("id")

def processP(node, data, classes, objects):
	path = ''
	obj = ''
	obj_type = ''
	for child in node.childNodes:
		if child.tagName == "code":
			for child1 in child.childNodes: 
				if child1.tagName == 'span' and child1.hasAttribute('itemprop') and child1.getAttribute('itemprop') == 'path':
					path = collect_text(child1)
				if child1.tagName == 'span' and child1.hasAttribute('itemprop') and child1.getAttribute('itemprop') == 'name':
					obj = collect_text(child1)
		if child.nodeType == child.TEXT_NODE:
			obj_type = child.nodeValue

	if path != '' and obj != '' and obj_type != '':
		arr_path = path.split('.')
		target = data
		for p in arr_path:
			if not p in target:
				target[p] = dict()
			target = target[p]
		arr_obj = obj.split('.')	
		if 'class' in obj_type:
			classes[obj] = path + '.' + obj
			for o in arr_obj:
				if not o in target:
					target[o] = dict()
				target = target[o]
			target["!url"] = docs_ref + "#" + obj
			target["prototype"] = dict()
			#target["!type"] = '?'	
		elif 'object' in obj_type:
			objects.append(obj)
			target = data['!define']
			for o in arr_obj:
				if not o in target:
					target[o] = dict()
				target = target[o]
			target["!url"] = docs_ref + "#" + obj
			#target["!type"] = 'Object'
		elif 'namespace' in obj_type:
			l_namespaces[obj] = path + '.' + obj
			for o in arr_obj:
				if not o in target:
					target[o] = dict()
				target = target[o]	
			target["!url"] = docs_ref + "#" + obj				

def processParameterOptions(options):
	res = list()
	if options.startswith("Array<"):
		t = processParameterOptions(options[len("Array<") : options.rindex(">")])
		for y in t:
			res.append("[" + y + "]")
	elif options.startswith("MVCArray<"):
		t = processParameterOptions(options[len("MVCArray<") : options.rindex(">")])
		for y in t:
			res.append("[" + y + "]")		
	else:
		a = options.split("|", 1)
		a0 = a[0]
		if a0 in l_classes.keys():
			a0 = l_classes[a0]
		res.append(a0)
		if len(a)>1:
			res.extend(processParameterOptions(a[1]))
	return res	

def processCallbackFunction(pfunc):
	param_str = pfunc[pfunc.index("(")+1 : pfunc.rindex(")")]
	l_opt = param_str.split(',')
	res = ''
	count = 0
	for o in l_opt:
		oo = re.split('(?![^<]*>)\|(?!=.*<)',o)
		if len(oo) == 1:
			oo = processParameterOptions(o)
		res += (', ' if res!='' else '') + 'p' + str(count) + ': ' + ('?' if len(oo)>1 else checkParameterType(oo[0].strip()))
		count += 1
	res = 'fn(' + res + ')'
	return res	

def checkParameterType(ptype):
	res = ptype
	if ptype == 'boolean':
		res = 'bool'
	elif ptype == 'Array':
		res = '[]'
	elif ptype == '*':
		res = '?'
	elif ptype.startswith('function'):
		res = processCallbackFunction(ptype)		
	return res		

def processReturnType(preturn):
	a = preturn.split("|")
	if len(a)>1:
		res = '?'
	elif preturn.startswith('Array<') or preturn.startswith('MVCArray<'):
		l = re.split('(?![^<]*>)\|(?!=.*<)', preturn)
		if len(l) == 1:
			l = processParameterOptions(preturn)
		if len(l)>1:
			res = 'Object'
		else:
			res = l[0]		
	else:
		res = checkParameterType(preturn)
	if res == '?':
		res = 'Object'	
	return res

def processFuncParameters(sparams):
	#arr_p = sparams.split(', ')
	arr_p = re.split("(?![^(]*\)),(?!=.*\()", sparams)
	d_params = dict()
	res = ''
	for p in arr_p:
		try:
			[k,v] = p.split(":")
		except:
			[k,v,r] = p.split(":")
		d_params[k] = re.split('(?![^<]*>)\|(?!=.*<)', v)
		if len(d_params[k]) == 1:	
			d_params[k] = processParameterOptions(v)
		res += (', ' if res!='' else '') + k.strip() + ': ' + ('?' if len(d_params[k])>1 else checkParameterType(d_params[k][0]))
	#print d_params
	return res	 

def getObject(obj):
	target = data_struc
	if obj in l_classes.keys():
		objfull = l_classes[obj]
	elif obj in l_namespaces.keys():
		objfull = l_namespaces[obj]	
	else:
		target = data_struc['!define']
		objfull = obj
	for x in objfull.split('.'):
		target = target[x]
	return target			

def processConstructor(obj, node):
	func = ''
	descr = ''
	#print "Process constructor"
	for child in node.childNodes:
		if child.tagName == 'tbody':
			for tr in child.childNodes:
				if tr.tagName == 'tr':
					count = 0
					for td in tr.childNodes:
						if td.tagName == 'td':
							if count == 0:
								func = collect_text(td)
							elif count == 1:
								descr = collect_text(td)
							count += 1	

	param_str = func[func.index("(")+1 : func.index(")")] 

	#print func
	#print param_str
	#print descr							 	

	resf = 'fn(' 
	if param_str != '':
		resf += processFuncParameters(param_str)
	resf += ') -> +' + l_classes[obj]

	target = getObject(obj)
	target['!type'] = resf
	target['!doc'] = descr 

def processMethods(obj, node):
	target = getObject(obj)
	for child in node.childNodes:
		if child.tagName == 'tbody':
			for tr in child.childNodes:
				if tr.tagName == 'tr':
					func = ''
					ftype = ''
					descr = ''
					count = 0
					for td in tr.childNodes:
						if td.tagName == 'td':
							if count == 0:
								func = collect_text(td)
							elif count == 1:
								for div in td.childNodes:
									if div.tagName == 'div':
										if div.hasAttribute("class") and div.getAttribute("class") == 'desc':
											descr = collect_text(div)
										else:
											for code in div.childNodes:
												if code.tagName == 'code':		 
													ftype = collect_text(code)
							count += 1	
					#print func		
					fname = func[0 : func.index("(")]		
					param_str = func[func.index("(")+1 : func.rindex(")")] 

					resf = 'fn(' 
					if param_str != '':
						#print param_str
						resf += processFuncParameters(param_str)
					resf += ')'
					if(ftype != 'None' and ftype != ''):	
						resf += ' -> ' + checkParameterType(l_classes[ftype] if ftype in l_classes.keys() else processReturnType(ftype))

					if not "prototype" in target:
						target["prototype"] = dict()	

					target["prototype"][fname] = dict()
					target["prototype"][fname]['!type'] = resf
					target["prototype"][fname]['!doc'] = descr	

def processProperties(obj, node):
	target = getObject(obj)
	for child in node.childNodes:
		if child.tagName == 'tbody':
			for tr in child.childNodes:
				if tr.tagName == 'tr':
					prop = ''
					ptype = ''
					pdescr = ''
					count = 0
					for td in tr.childNodes:
						if td.tagName == 'td':
							if count == 0:
								prop = collect_text(td)
							elif count == 1:
								for div in td.childNodes:
									if div.tagName == 'div':
										if div.hasAttribute("class") and div.getAttribute("class") == 'desc':
											pdescr = collect_text(div)
										else:
											for code in div.childNodes:
												if code.tagName == 'code':		 
													ptype = collect_text(code)	
							count += 1	
					#print prop		

					p_type = checkParameterType(l_classes[ptype] if ptype in l_classes.keys() else processReturnType(ptype))

					if not "prototype" in target:
						target["prototype"] = dict()	

					target["prototype"][prop] = dict()
					target["prototype"][prop]['!type'] = p_type
					target["prototype"][prop]['!doc'] = pdescr

def processEvents(obj, node):
	target = data_struc['!define']
	for child in node.childNodes:
		if child.tagName == 'tbody':
			for tr in child.childNodes:
				if tr.tagName == 'tr':
					event = ''
					count = 0
					for td in tr.childNodes:
						if td.tagName == 'td':
							if count == 0:
								event = collect_text(td)
							count += 1	
					#print event		

					if not event in target:
						target[event] = "string"	

def processConstants(obj, node):
	target = getObject(obj)
	for child in node.childNodes:
		if child.tagName == 'tbody':
			for tr in child.childNodes:
				if tr.tagName == 'tr':
					cnst = ''
					descr = ''
					count = 0
					for td in tr.childNodes:
						if td.tagName == 'td':
							if count == 0:
								cnst = collect_text(td)
							elif count == 1:
								descr = collect_text(td)
							count += 1	
					#print cnst		

					target[cnst] = dict()
					target[cnst]['!type'] = "string"
					target[cnst]['!doc'] = descr

def processStaticMethods(obj, node):
	target = getObject(obj)
	for child in node.childNodes:
		if child.tagName == 'tbody':
			for tr in child.childNodes:
				if tr.tagName == 'tr':
					func = ''
					ftype = ''
					descr = ''
					count = 0
					for td in tr.childNodes:
						if td.tagName == 'td':
							if count == 0:
								func = collect_text(td)
							elif count == 1:
								for div in td.childNodes:
									if div.tagName == 'div':
										if div.hasAttribute("class") and div.getAttribute("class") == 'desc':
											descr = collect_text(div)
										else:
											for code in div.childNodes:
												if code.tagName == 'code':		 
													ftype = collect_text(code)	
							count += 1	
					#print func		
					fname = func[0 : func.index("(")]		
					param_str = func[func.index("(")+1 : func.rindex(")")] 

					resf = 'fn(' 
					if param_str != '':
						#print param_str
						resf += processFuncParameters(param_str)
					resf += ')'
					if(ftype != 'None' and ftype != ''):	
						resf += ' -> ' + checkParameterType(l_classes[ftype] if ftype in l_classes.keys() else processReturnType(ftype))

					target[fname] = dict()
					target[fname]['!type'] = resf
					target[fname]['!doc'] = descr					

def processOneRefObject(node, data, classes, objects):
	for child in node.childNodes:
		if child.tagName == 'h2' and child.hasAttribute('id'):
			processH2(child, data, classes, objects)
		if child.tagName == 'p':
			processP(child, data, classes, objects)	

def processOneRefObjectTables(node):
	for child in node.childNodes:
		if child.tagName == 'table' and child.hasAttribute('summary'):
			s = child.getAttribute('summary')	
			arr_s = s.split()
			obj = arr_s[1] if len(arr_s)>1 else None
			t = arr_s[3] if len(arr_s)>3 else None
			if not obj is None:
				#print t
				if t == 'Constructor':
					processConstructor(obj, child)
				elif t == 'Methods':
					processMethods(obj, child)	
				elif t == 'Properties':
					processProperties(obj, child)
				elif t == 'Events':
					processEvents(obj, child)
				elif t == 'Constants':
					processConstants(obj, child)
				elif t == 'Static':
					processStaticMethods(obj, child)		


docs_ref = "https://developers.google.com/maps/documentation/javascript/reference"

sock = urllib.urlopen(docs_ref)
htmlSource = sock.read()
sock.close()

doc = libxml2dom.parseString(htmlSource, html=1)

data_struc = dict()
data_struc["!name"] = "googlemapsjsv3"
data_struc["!define"] = dict()
data_struc["google"] = dict()
data_struc["google"]["maps"] = dict()
data_struc["google"]["maps"]["version"] = "string" 

l_objects = list()
l_classes = dict()
l_namespaces = dict()

content = doc.getElementById("gc-wrapper")


#doc.getElementsByClassName("devsite-article-body")

wrapper = None
for node in content.childNodes:
	if node.tagName == 'div' and node.hasAttribute('class') and node.getAttribute('class')=='devsite-main-content clearfix':
		for n1 in node.childNodes:
			if n1.tagName == 'article':
				for n2 in n1.childNodes:
					if n2.tagName == 'div' and n2.hasAttribute('class') and n2.getAttribute('class')=='devsite-article-inner':
						for n3 in n2.childNodes:
							if n3.tagName == 'div' and n3.hasAttribute('itemprop') and n3.getAttribute('itemprop')=='articleBody':
								wrapper = n3
								break

print wrapper

if wrapper is not None:
	for node in wrapper.childNodes:
		if node.tagName == 'div' and node.hasAttribute('itemscope') and node.hasAttribute('itemtype') and node.getAttribute('itemtype') == 'http://developers.google.com/ReferenceObject':
			processOneRefObject(node, data_struc, l_classes, l_objects) 

	#print l_classes		

	for node in wrapper.childNodes:
		if node.tagName == 'div' and node.hasAttribute('itemscope') and node.hasAttribute('itemtype') and node.getAttribute('itemtype') == 'http://developers.google.com/ReferenceObject':
			processOneRefObjectTables(node)		

str_json = json.dumps(data_struc, sort_keys=True, indent=4, separators=(',', ': '))

#print l_namespaces

# Open a file
fo = open("_googlemapsjsv3.json", "w")
fo.write(str_json);
# Close the file
fo.close()
