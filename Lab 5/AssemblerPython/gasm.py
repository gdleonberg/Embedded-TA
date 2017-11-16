##---------------------------------------------------------------
# Written by Gregory Leonberg for 332:493:02 "Embedded Systems Design"
# Fall 2017 Semester
# Converts custom GRISC ISA assembly into binary COE file
##---------------------------------------------------------------

##---------------------------------------------------------------
# format of input file is:
# [ignored lines]
# .data
# data segement
# .text
# text segement
##---------------------------------------------------------------

##---------------------------------------------------------------
# format of data segment is:
# [blank]                   OR
# // comment                OR
# label: [type] [value] // comment
# types are str or num
# [where comments are optional]
# [one operation or label per line]
# ignores whitespace
# assumes correct input, does not handle invalid assembly
##---------------------------------------------------------------

##---------------------------------------------------------------
# format of text segment is:
# [blank]                   OR
# // comment                OR
# opcode args // comment    OR
# label: // comment
# [where comments are optional]
# [one operation or label per line]
# ignores whitespace
# assumes correct input, does not handle invalid assembly
##---------------------------------------------------------------

from tkinter import filedialog
from tkinter import *

#################################################################

def assembler():
	
	# open input file
	sourceName = askOpen()
	source = open(sourceName, 'r')
	
	# open output files
	dataName = askSaveData()
	data = open(dataName, 'w')
	textName = askSaveText()
	text = open(textName, 'w')
	
	# go through input file, strip out all comments and spacing
	cleaned = list()
	for line in source:
		clean = line.strip().split("//")[0].strip()
		if clean:
			cleaned.append(clean)
	
	# go through cleaned up lines, split into data and text segments
	dStart = 1
	while cleaned[dStart-1] != '.data':
		dStart = dStart + 1
	tStart = dStart + 1
	while cleaned[tStart-1] != '.text':
		tStart = tStart + 1
	dataLines = cleaned[dStart:tStart-1]
	textLines = cleaned[tStart:]
	
	# build labels from data segment
	dLabels = dataLabels(dataLines)
	
	# convert data segment to binary COE file string array
	dataConvertedArr = buildDataCoe(dataLines)
	
	# build labels from instruction segment
	tLabels, textLines = textLabels(textLines)
	
	# convert text segment to binary COE file string array
	textConvertedArr = buildTextCoe(textLines, dLabels, tLabels)
	
	# write data segment to COE file
	for line in dataConvertedArr:
		data.write(line + '\n')
	
	# write text segment to COE file
	for line in textConvertedArr:
		text.write(line + '\n')
	
	return True

#################################################################

def dataLabels(dataLines):
	
	labels = {}
	counter = 0
	for line in dataLines:
		tag = line.split(':')[0]
		rest = line.split(':')[1]
		typ = rest.split()[0]
		val = rest.split(typ)[1].strip()
		
		if typ == 'str':
			val = val.split('"')[1]
			val = val.split('"')[0]
		
		labels[tag] = dec2bin(counter, 16)
		if typ == 'str':
			counter = counter + len(val) + 1
		else:
			counter = counter + 1
	return labels

def buildDataCoe(dataLines):
	
	lines = list()
	lines.append('MEMORY_INITIALIZATION_RADIX=2;')
	lines.append('MEMORY_INITIALIZATION_VECTOR=')
	
	for lineNum in range(len(dataLines)):
		line = dataLines[lineNum]
		tag = line.split(':')[0]
		rest = line.split(':')[1]
		typ = rest.split()[0]
		val = rest.split(typ)[1].strip()
		
		if typ == 'str':
			val = val.split('"')[1]
			val = val.split('"')[0]
			for char in val:
				lines.append(dec2bin(ord(char), 16) + ",")
			if lineNum < len(dataLines)-1:
				lines.append(dec2bin(0, 16) + ",")
			else:
				lines.append(dec2bin(0, 16) + ";")
		else:
			val = int(val)
			if lineNum < len(dataLines)-1:
				lines.append(dec2bin(val, 16) + ",")
			else:
				lines.append(dec2bin(val, 16) + ";")
	
	return lines

def textLabels(textLines):
	
	newLines = list()
	labels = {}
	counter = 0
	
	for line in textLines:
		if ":" in line:
			tag = line.split(':')[0]
			labels[tag] = dec2bin(counter, 16)
		else:
			newLines.append(line)
			counter = counter + 1
	
	return labels, newLines

def buildTextCoe(textLines, dLabels, tLabels):
	
	lines = list()
	lines.append('MEMORY_INITIALIZATION_RADIX=2;')
	lines.append('MEMORY_INITIALIZATION_VECTOR=')
	
	for lineNum in range(len(textLines)):
		
		ops, types, regs = buildDicts()
		
		args = textLines[lineNum].strip().split()
		opcode = args[0]
		numArgs = len(args)
		
		binop = ops[opcode]
		optype = types[binop[0:2]]
		command = binop
		
		# convert R-type
		if(optype == 'r'):
			for j in range(1, numArgs):
				command = command + regs[args[j]];
		
		# convert I-type
		elif(optype == 'i'):
			if(opcode == 'la'): # la pseudo-instruction as ori
				command = command + regs[args[1]] + regs['$zero'] + dLabels[args[2]]
			elif((opcode == 'lw') or (opcode == 'sw')):
				command = command + regs[args[1]] + regs[args[2]] + dLabels[args[3]]
			elif((opcode == 'beq') or (opcode == 'bne')):
				command = command + regs[args[1]] + regs[args[2]] + tLabels[args[3]]
			else:
				command = command + regs[args[1]] + regs[args[2]] + dec2bin(int(args[3]), 16)
		
		# convert J-type
		else:
			if((opcode == 'j') or (opcode == 'jal')):
				command = command + tLabels[args[1]]
			else:
				command = command + dec2bin(int(args[2]), 16)
		
		# pad command on the right to 32 bits
		command = command.ljust(32, '0')
		
		# write command to COE file list
		if lineNum < len(textLines)-1:
			lines.append(command + ",")
		else:
			lines.append(command + ";")
		
	return lines

def dec2bin(num, digits):
	ret = bin(num)
	ret = ret[2:]
	ret = ret.zfill(digits)
	return ret

def askOpen():
	root = Tk()
	root.filename = filedialog.askopenfilename(initialdir = "/",title = "Select source file",filetypes = (("assembly source","*.txt"),("all files","*.*")))
	return root.filename

def askSaveData():
	root = Tk()
	root.filename =  filedialog.asksaveasfilename(initialdir = "/",title = "Select data output file",filetypes = (("COE files","*.coe"),("all files","*.*")))
	return root.filename

def askSaveText():
	root = Tk()
	root.filename =  filedialog.asksaveasfilename(initialdir = "/",title = "Select text output file",filetypes = (("COE files","*.coe"),("all files","*.*")))
	return root.filename

def buildDicts():
	# define opcode constants in associative array (dictonary)
	ops = {};
	ops['add'] = '00000'
	ops['sub'] = '00001'
	ops['sll'] = '00010' 
	ops['srl'] = '00011'
	ops['sra'] = '00100'
	ops['and'] = '00101'
	ops['or'] = '00110'
	ops['xor'] = '00111'
	ops['slt'] = '01000'
	ops['sgt'] = '01001'
	ops['seq'] = '01010'
	ops['send'] = '01011'
	ops['recv'] = '01100'
	ops['jr'] = '01101'
	ops['wpix'] = '01110'
	ops['rpix'] = '01111'
	ops['beq'] = '10000'
	ops['bne'] = '10001'
	ops['ori'] = '10010'
	ops['lw'] = '10011'
	ops['sw'] = '10100'
	ops['j'] = 	'11000'
	ops['jal'] = '11001'
	ops['clrscr'] = '11010'
	ops['la'] = '10010' # pseudo instruction for ori with label as immediate
	
	# define instruction type decoding in associative array (dictionary)
	types = {};
	types['00'] = 'r';
	types['01'] = 'r';
	types['10'] = 'i';
	types['11'] = 'j';
	
	# define register constants in associative array (dictionary)
	regs = {};
	regs['$zero'] = '00000'
	regs['$pc'] = '00001'
	regs['$ra'] = '00010'
	for i in range(3, 32):
		st = '$r' + str(i)
		regs[st] = dec2bin(i, 5)
	
	return ops, types, regs

if __name__ == '__main__':
	success = assembler()
