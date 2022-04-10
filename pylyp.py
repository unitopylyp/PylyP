#!/usr/bin/env python3

import sys
import ast
import symtable
import os

additional_args = []

compiler_commands = ["-d", "-debug", "-v", "-visualize", "-ne", "-noexec"]
#Commenti di debug
comments = False
#Visualizzazione dell'AST
visualize = False
#Analizza senza eseguire il codice
noexec = False

def print_instructions():
	print("usage: pylyp [code.py] [options]")
	print("options:")
	print("-debug (or -d):	" + "Show errors on non-reversible instructions")
	print("-visualize (or -v): " + "Show the AST")
	print("-noexec(or -ne): " + "Just analyze without running the code")
	print("Using 'pylyp' command without any code or options is the equivalent")
	print("of calling the 'python' command")

l = len(sys.argv)

if l == 1:
	cmd = f'start cmd.exe @cmd /k python'
	os.system(cmd)
	
else:
	#Parsificazione degli argomenti
	firstarg = (sys.argv[1])

	if l > 2:
		i = 2
		while(i < l):
			if sys.argv[i] in compiler_commands:
				if sys.argv[i] == "-d" or sys.argv[i] == "-debug":
					comments = True
				elif sys.argv[i] == "-v" or sys.argv[i] == "-visualize":
					visualize = True
				elif sys.argv[i] == "-ne" or sys.argv[i] == "-noexec":
					noexec = True
				elif sys.argv[i] == "-h" or sys.argv[i] == "-help":
					print_instructions()
				else:
					print("Unexpected error in additional arguments!")
			else:
				print_instructions()
			i += 1
	#Lettura del codice da parsificare
	f = open(firstarg, "r")
	code = f.read()
	f.close()
	   
	#Lista di funzioni accettate a priori come reversibili
	rev_functions = ["range"]
	
	print("<PylyP>\n")
	
	st1 = symtable.symtable(code, 'sym_table', 'exec')
	sub_st1 = st1.get_children()
	is_close_symtable = {}

	for child in sub_st1:
		if str(child.get_type()) == 'function':
			is_close_symtable.update({child.get_name() : False})
			global_list = list(child.get_globals())
			#Controllo se ho tovato funzioni presenti in rev_functions
			for f in rev_functions:
				if f in global_list:
					global_list.remove(f)
			if global_list:
				is_close_symtable.update({child.get_name() : False})
			else:
				is_close_symtable.update({child.get_name() : True})			

	fun_count = 0
	tree_ast = ast.parse(code, mode="exec")
	super_nodes = [node for node in ast.walk(tree_ast)]
	for super_n in super_nodes:
		if isinstance(super_n, ast.FunctionDef):
			print("\t<" + super_n.name + ">")
			is_reversible = True
			nodes = [node for node in ast.walk(super_n)]
			for n in nodes:				
				if isinstance(n, ast.Assign):
					#Controllo assegnazioni multiple
					for target in n.targets:
						if not isinstance(target, ast.Name):
							if comments:
								print("\t\tAt line: ", target.lineno)
								print("\t\tMultiple assignment is not allowed\n")
							is_reversible = False
					#Controllo se non ho <var> = <const>
					if not isinstance(n.value, ast.Constant):
						if isinstance(n.value, ast.BinOp):
							try:
								#Controllo <var> = <var> ...
								if n.value.left.id != target.id:
									if comments:
										print("\t\tAt line: ", n.lineno)
										print("\t\tThis type of assignment is not allowed\n")
									is_reversible = False
								#Controllo <var> = <var> + ... | <var> - ...
								elif not(isinstance(n.value.op, ast.Add) or isinstance(n.value.op, ast.Sub)):
									if comments:
										print("\t\tAt line: ", n.lineno)
										print("\t\tThis type of assignment is not allowed\n")
									is_reversible = False
								#Controllo <var> = <var> + 1 | <var> - 1
								elif n.value.right.value != 1:
									if comments:
										print("\t\tAt line: ", n.lineno)
										print("\t\tThis type of assignment is not allowed\n")
									is_reversible = False
							except:
								if comments:
									print("\t\tAt line: ", n.lineno)
									print("\t\tThis type of assignment is not allowed\n")
								is_reversible = False
						#Non ho Un'operazione binaria a destra dell'assegnazione
						#controllo se ho una costante negativa
						elif isinstance(n.value, ast.UnaryOp):
							if (not isinstance(n.value.op, ast.USub)) or (not isinstance(n.value.operand, ast.Constant)):
								if comments:
									print("\t\tAt line: ", n.lineno)
									print("\t\tThis type of assignment is not allowed\n")
								is_reversible = False
						#L'assegnazione non si comporta seguendo le regole della grammatica
						else:
							if comments:
								print("\t\tAt line: ", n.lineno)
								print("\t\tThis type of assignment is not allowed\n")
							is_reversible = False
				if isinstance(n, ast.AugAssign):
					#Controllo se ho un += o un -=
					if not(isinstance(n.op, ast.Add) or isinstance(n.op, ast.Sub)):
						if comments:
							print("\t\tAt line: ", n.lineno)
							print("\t\t*= and /= operation are not allowed\n")
						is_reversible = False
					#Non ho una costante a destra dell'assegnazione aumentata
					if not(isinstance(n.value, ast.Constant)):
						if comments:
							print("\t\tAt line: ", n.lineno)
							print("\t\tTo the right of an augmented assignment there must be a 1\n")
						is_reversible = False
					#Controllo se ho un 1 a destra dell'assegnazione aumentata
					else:
						if n.value.value != 1:
							if comments:
								print("\t\tAt line: ", n.lineno)
								print("\t\tTo the right of an augmented assignment there must be a 1\n")
							is_reversible = False
				#La grammatica non prevede while
				if isinstance(n, ast.While):
					if comments:
						print("\t\tAt line: ", n.lineno)
						print("\t\tThe while loop is not reversible")
					is_reversible = False
				#La grammatica non prevede operatori ternari
				if isinstance(n, ast.IfExp):
					if comments:
						print("\t\tAt line: ", n.lineno)
						print("\t\tThis type of construct is not allowed,\n\t\tplease use the standard if else construct\n")
					is_reversible = False
				#Controllo il costrutto if
				if isinstance(n, ast.If):
					#Salvo tutti gli identificatori presenti nella guardia
					cond_var = []
					bodyelse_var = []
					tmp_tree = ast.dump(n.test)
					strp = str(tmp_tree)
					strp_save = strp
					while "id='" in strp:
						strp = strp.split("id='",1)[1]
						cond_var.append(strp)
					count = 0
					for s in cond_var:
						s = cond_var[count]
						x = str(s)
						x = x.partition("'")[0]
						cond_var[count] = x
						count += 1
					cond_var = list(set(cond_var))
					#Navigo nei nodi figli della condizione e controllo che non vengano
					#effettuate delle modifiche alle variabili presenti nella guardia
					subNodes = [node for node in ast.walk(n)]
					for sub_n in subNodes:
						if isinstance(sub_n, ast.Assign):
							for target in sub_n.targets:
								bodyelse_var.append(target.id)
						if isinstance(sub_n, ast.AugAssign):
								bodyelse_var.append(sub_n.target.id)
					bodyelse_var = list(set(bodyelse_var))
					intersect = list(set(bodyelse_var).intersection(cond_var))
					if intersect:
						if comments:
							print("\t\tAt line: ", n.lineno)
							print("\t\tThe variables inside the condition of the if statement \n\t\tare changed in the body or in the body of the else\n")
						is_reversible = False
				#Controllo il costrutto for
				if isinstance(n, ast.For):
					#Salvo tutti gli identificatori presenti nella guardia
					cond_var = []
					bodyelse_var = []
					tmp_tree = ast.dump(n.target)
					strp = str(tmp_tree)
					strp_save = strp
					while "id='" in strp:
						strp = strp.split("id='",1)[1]
						cond_var.append(strp)
					count = 0
					for s in cond_var:
						s = cond_var[count]
						x = str(s)
						x = x.partition("'")[0]
						cond_var[count] = x
						count += 1
					#Salvo anche la variabile su cui si cicla (se presente)
					if isinstance(n.iter, ast.Name):
						cond_var.append(n.iter.id)
					cond_var = list(set(cond_var))
					#Navigo nei nodi figli della condizione e controllo che non vengano
					#effettuate delle modifiche alle variabili presenti nella guardia
					subNodes = [node for node in ast.walk(n)]
					for sub_n in subNodes:
						if isinstance(sub_n, ast.Assign):
							for target in sub_n.targets:
								bodyelse_var.append(target.id)
						if isinstance(sub_n, ast.AugAssign):
								bodyelse_var.append(sub_n.target.id)
					bodyelse_var = list(set(bodyelse_var))
					intersect = list(set(bodyelse_var).intersection(cond_var))
					if intersect:
						if comments:
							print("\t\tAt line: ", n.lineno)
							print("\t\tThe target variable or the iter variable of the for statement \n\t\tis changed in the body or in the body of the else\n")
						is_reversible = False
			if comments and not is_close_symtable.get(super_n.name):
				print("\t\tThe function \"" + super_n.name + "\" is not closed\n")
			is_reversible  = is_reversible and is_close_symtable.get(super_n.name)			  
			print("\t\tFunction: \"" + super_n.name + "\", reversibility:", is_reversible)
			print("\t</" + super_n.name + ">\n")
			fun_count += 1
	print("</PylyP>")
	print()
	tree = ast.dump(tree_ast, indent=4)
	if visualize:
		print("<ast>")
		print(tree)
		print("</ast>\n")
	if not noexec:
		output = compile(tree_ast, sys.argv[1],'exec')
		exec(output)   
	



