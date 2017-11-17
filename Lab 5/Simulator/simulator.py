##---------------------------------------------------------------
# Written by Gregory Leonberg for 332:493:02 "Embedded Systems Design"
# Fall 2017 Semester
# Simulates GRISC ISA assembly
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

##---------------------------------------------------------------
# Requires Python 3
# Requires Pillow package (pip install Pillow)
# Requires numpy package
##---------------------------------------------------------------

from tkinter import filedialog
from tkinter import *
from time import sleep
from PIL import Image
import numpy as np
import threading

framebuffer = list()
for i in range(2**16):
	framebuffer.append(0)

#################################################################

def simulator():
	
	# prompt for assembly source file
	sourceName = askOpen()
	source = open(sourceName, 'r')
	
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
	
	# build labels from data segment, initialize data memory
	dLabels, dMem = dataSegment(dataLines)
	
	# build labels from instruction segment
	tLabels, textLines = textLabels(textLines)
	
	# build register file and initialize to zero
	regs = {};
	regs['$zero'] = 0
	regs['$pc'] = 0
	regs['$ra'] = 0
	for i in range(3, 32):
		st = '$r' + str(i)
		regs[st] = 0
	
	# interpret instructions
	interpret(textLines, regs, dMem, tLabels, dLabels)
	
	return True

#################################################################

def askOpen():
	root = Tk()
	root.filename = filedialog.askopenfilename(initialdir = "/",title = "Select source file",filetypes = (("assembly source","*.txt"),("all files","*.*")))
	root.destroy()
	return root.filename

def dec2bin(num, digits):
	ret = bin(num)
	ret = ret[2:]
	ret = ret.zfill(digits)
	return ret

def bin2dec(binary):
	return int(binary, 2)

def interpret(textLines, regs, dMem, tLabels, dLabels):
	
	# display cleaned instructions
	print("Parsed instructions:")
	for i in range(len(textLines)):
		print("[" + str(i) + "]: " + textLines[i])
	print("")
	
	# ask for break points desired by user
	print("Please enter desired breakpoints:\n(one at a time as integers, negative number to finish)")
	bPoints = list()
	bPoints.append(-1)
	bPoint = int(input("Breakpoint: "))
	while bPoint >= 0:
		bPoints.append(bPoint)
		bPoint = int(input("Breakpoint: "))
	
	# split off thread for display
	t1 = threading.Thread(target=display)
	t1.daemon = True
	t1.start()
	
	# loop across instructions
	step = False
	i = 0
	counter = 0
	while i != len(textLines):
		
		# if line is breakpoint, trigger user command shell
		if (i in bPoints) or step:
			bPoints, step, dMem, regs = shell(textLines, regs, dMem, bPoints, step, tLabels, dLabels)
			i = regs['$pc']
		
		# execute instruction
		regs, dMem = execute(textLines[i], regs, dMem, tLabels, dLabels)
		i = regs['$pc']
		regs['$zero'] = 0

def execute(instruction, regs, dMem, tLabels, dLabels):
	
	global framebuffer
	args = instruction.strip().split()
	instruction = args[0]
	regs['$pc'] = regs['$pc'] + 1
	
	if instruction == "add":
		temp = regs[args[2]] + regs[args[3]]
		if temp > 2**16:
			temp = temp - 2**16
		regs[args[1]] = temp
	elif instruction == "sub":
		temp = regs[args[2]] - regs[args[3]]
		if temp < 0:
			temp = 2**16 - temp
		regs[args[1]] = temp
	elif instruction == "sll":
		temp = regs[args[2]] * 2
		if temp > 2**16:
			temp = temp - 2**16
		regs[args[1]] = temp
	elif (instruction == "srl") or (instruction == "sra"):
		regs[args[1]] = int(regs[args[2]] + regs[args[3]])
	elif instruction == "and":
		regs[args[1]] = int(regs[args[2]] & regs[args[3]])
	elif instruction == "or":
		regs[args[1]] = int(regs[args[2]] | regs[args[3]])
	elif instruction == "xor":
		regs[args[1]] = int(regs[args[2]] ^ regs[args[3]])
	elif instruction == "slt":
		if regs[args[2]] < regs[args[3]]:
			temp = 1
		else:
			temp = 0
		regs[args[1]] = temp
	elif instruction == "sgt":
		if regs[args[2]] > regs[args[3]]:
			temp = 1
		else:
			temp = 0
		regs[args[1]] = temp
	elif instruction == "seq":
		if regs[args[2]] == regs[args[3]]:
			temp = 1
		else:
			temp = 0
		regs[args[1]] = temp
	elif instruction == "send":
		print(str(chr(regs[args[1]])))
	elif instruction == "recv":
		regs[args[1]] = ord(input("Enter a character to be read: ")[0])
	elif instruction == "jr":
		regs['$pc'] = regs[args[1]]
	elif instruction == "wpix":
		framebuffer[regs[args[1]]] = regs[args[2]]
	elif instruction == "rpix":
		regs[args[1]] = frambuffer[regs[args[2]]]
	elif instruction == "beq":
		if regs[args[1]] == regs[args[2]]:
			regs['$pc'] = bin2dec(tLabels[args[3]])
	elif instruction == "bne":
		if regs[args[1]] != bin2dec(tLabels[args[2]]):
			regs['$pc'] = int(args[3])
	elif instruction == "ori":
		regs[args[1]] = regs[args[2]] | int(args[3])
	elif instruction == "la":
		regs[args[1]] = bin2dec(dLabels[args[2]])
	elif instruction == "lw":
		regs[args[1]] = dMem[regs[args[2]] + bin2dec(dLabels[args[3]])]
	elif instruction == "sw":
		dMem[regs[args[2]] + int(args[3])] = regs[args[1]]
	elif instruction == "j":
		regs['$pc'] = bin2dec(tLabels[args[1]])
	elif instruction == "jal":
		regs['$ra'] = regs['$pc']
		regs['$pc'] = bin2dec(tLabels[args[1]])
	elif instruction == "clrscr":
		for i in range(len(framebuffer)):
			framebuffer[i] = int(args[1])
	
	return regs, dMem

def shell(textLines, regs, dMem, bPoints, step, tLabels, dLabels):
	
	global framebuffer
	
	i = regs['$pc']
	
	if step:
		# reset step flag
		step = False
	
	else:
		# print command list
		print("Breakpoint encountered at line: " + str(i) + "\n")
		print("Options:")
		print("\tShow program ('prg')")
		print("\tShow data labels ('dlabels')")
		print("\tShow text labels ('tlabels')")
		print("\tShow instruction ('instr')")
		print("\tShow registers ('regs')")
		print("\tShow breakpoints ('bps')")
		print("\tAdd breakpoint ('addbp')")
		print("\tRemove breakpoint ('rmbp')")
		print("\tStep a single instruction ('step')")
		print("\tPeek at video memory ('vPeek')")
		print("\tPeek at data memory ('dPeek')")
		print("\tPoke a register value ('rPoke')")
		print("\tPoke a video memory value ('vPoke')")
		print("\tPoke a data memory value ('dPoke')")
		print("\tExit debug shell ('exit')\n\n")
	
	choice = ""
	while (choice != "exit") and (choice != "step"):
	
		# read command
		choice = input("Enter your choice: ")
		choice = choice.strip()
		print("")
	
		# act based on command
		if choice == "prg":
			print("Parsed instructions:")
			for j in range(len(textLines)):
				print("[" + str(j) + "]: " + textLines[j])
			print("")
		elif choice == "dlabels":
			for label in dLabels:
				print(label + ": [" + str(bin2dec(dLabels[label])) + "]")
			print("")
		elif choice == "tlabels":
			for label in tLabels:
				print(label + ": [" + str(bin2dec(tLabels[label])) + "]")
			print("")
		elif choice == "instr":
			print(textLines[i] + "\n")
		elif choice == "regs":
			rs = list()
			rs.append('$zero')
			rs.append('$pc')
			rs.append('$ra')
			for r in range(3, 32):
				rs.append('$r' + str(r)) 
			for r in rs:
				print (r,'\t:', regs[r])
			print("")
		elif choice == "bps":
			for point in bPoints:
				if point >= 0:
					print("[" + str(point) + "]")
			print("")
		elif choice == "addbp":
			bPoint = int(input("Breakpoint: "))
			if bPoint not in bPoints:
				bPoints.append(bPoint)
			print("")
		elif choice == "rmbp":
			bPoint = int(input("Breakpoint: "))
			if bPoint in bPoints:
				bPoints.remove(bPoint)
			print("")
		elif choice == "vPeek":
			addr = int(input("Enter an address [0, 4095]: "))
			if (addr >= 0) and (addr < 4096):
				getRGBShell(addr)
			print("")
		elif choice == "dPeek":
			addr = int(input("Enter an address [0, 65535]: "))
			if (addr >= 0) and (addr < 65536):
				print("dMem[" + str(addr) + "] = " + str(dMem[addr]) + "\n")
		elif choice == "rPoke":
			addr = (input("Enter a register name: "))
			addr = addr.strip()
			val = int(input("Enter a value in decimal: "))
			if addr in list(regs.keys()):
				regs[addr] = val
		elif choice == "vPoke":
			addr = int(input("Enter an address [0, 4095]: "))
			val = int(input("Enter a value in decimal: "))
			if (addr >= 0) and (addr < 4096):
				framebuffer[addr] = val
		elif choice == "dPoke":
			addr = int(input("Enter an address [0, 65535]: "))
			val = int(input("Enter a value in decimal: "))
			if (addr >= 0) and (addr < 65536):
				dMem[addr] = val
		elif choice == "step":
			step = True
	
	# wait for resume
	input("Press enter to continue program execution: ")
	print("")
	return bPoints, step, dMem, regs

def display():
	
	global framebuffer
	
	data = np.zeros((64, 64, 3), dtype=np.uint8)
	
	# infinite loop of updating frame and then waiting 1/60 seconds
	while True:
		
		# write pixel values to image object
		for row in range(64):
			for col in range(64):
				pixel = dec2bin(framebuffer[row + col*64], 16)
				r = 255*(bin2dec(pixel[:5]) / 32)
				g = 255*(bin2dec(pixel[5:11]) / 64)
				b = 255*(bin2dec(pixel[11:]) / 32)
				
				data[row][col] = [r, g, b]
		
		img = Image.fromarray(data, 'RGB')
		img.save('temp.png')
		# img.show() WINDOWS 8 PHOTO VEIWER HIJACKS MY DESKTOP
		# MIGHT WORK BETTER FOR OTHER OS'S
		
		# wait for next frame time (currently set to 1 fps) 
		sleep(1.0)

def getRGBShell(addr):
	
	global framebuffer
	
	pixel = dec2bin(framebuffer[addr], 16)
	
	print("Decimal Pixel = " + str(framebuffer[addr]))
	print("Pixel = " + pixel)
	
	print("r = " + pixel[:5])
	print("g = " + pixel[5:11])
	print("b = " + pixel[11:])

def dataSegment(dataLines):
	
	dMem = list()
	for i in range(0, 2**16):
		dMem.append(0)
	
	labels = {}
	counter = 0
	
	for line in dataLines:
		tag = line.split(':')[0]
		rest = line.split(':')[1]
		typ = rest.split()[0]
		val = rest.split(typ)[1].strip()
		
		labels[tag] = dec2bin(counter, 16)
		
		if typ == 'str':
			val = val.split('"')[1]
			val = val.split('"')[0]
			for char in val:
				dMem[counter] = ord(char)
				counter = counter + 1
			dMem[counter] = 0
			counter = counter + 1
		else:
			dMem[counter] = int(val)
			counter = counter + 1
	return labels, dMem

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

if __name__ == '__main__':
	success = simulator()
