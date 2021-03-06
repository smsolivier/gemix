#!/usr/bin/env python3 

import numpy as np 
import os 
import sys 

def readInterp(dr):
	dr += '/'
	dist = sorted(os.listdir(dr)) # distance subdirectories in dr 

	for i in range(len(dist)):
		currentDir = dr + dist[i] + '/'
		uf = np.loadtxt(currentDir+'U')
		kf = np.loadtxt(currentDir+'k')
		cf = np.loadtxt(currentDir+'C')

		plt.plot(cf[:,0], cf[:,1])

	plt.show()

def interpolate(xinterp, r, val):
	N = len(val)

	# get two nearest points, want them to straddle xinterp 
	indx = np.argmin(np.fabs(r[:,0] - xinterp))
	x1 = r[indx,0] # closest value 
	x2 = r[indx+1,0] # next value up 
	if (x1 > xinterp): # make sure x1 and x2 straddle xinterp 
		x2 = r[indx-1,0]

	print('interpolating', xinterp, 'between', x1, x2)

	# get z index for 3D 
	zwidth = 0 # width of domain in z 
	indz = np.argmin(np.fabs(r[:,2] - zwidth))
	z = r[indz, 2] # closest z value to zwidth 

	y1 = [] # store values at x1 
	y2 = [] # store values at x2

	val1 = [] # store val at x = x1 
	val2 = [] # store val at x = x2 

	for i in range(N):
		# test for x = x1 
		if (r[i,0] == x1 and r[i,2] == z):
			y1.append(r[i,1]) # append y value 
			val1.append(val[i]) # append val

		# test for x = x2 
		elif (r[i,0] == x2 and r[i,2] == z):
			y2.append(r[i,1]) # store y value 
			val2.append(val[i]) # store val 

	# convert to numpy arrays 
	y1 = np.array(y1)
	y2 = np.array(y2)

	val1 = np.array(val1)
	val2 = np.array(val2) 

	# interpolate 
	# y = (y2 - y1)/(x2 - x1) * (x - x1) + y1 
	valinterp = (val2 - val1)/(x2 - x1) * (xinterp - x1) + val1 

	return y1, valinterp

def parse(xinterp, PLOT=False):
	''' parses OpenFOAM time directories and interpolates the y 
		velocity profile using the writeCellCentres output. 

		Inputs:
			xinterp:
				x value to interpolate at 
			PLOT: 
				plots the Ux profile if true 

		Outputs:
			y1: 
				y values where velocity is calculated 
			uinterp:
				interpolated Ux points 
			kinterp:
				interpolated k points 
			Cinterp:
				interpolated concentration points 
	''' 

	tdir = '0'
	# find highest time directory 
	for f in os.listdir('.'):
		if (f[0].isdigit() and os.path.isdir(f)):
			if (float(f) > float(tdir)):
				tdir = f 
	tdir += '/'

	print('using time directory ' + tdir)

	initDir = '0/' # place where cell centers are stored 

	# --- get velocities --- 
	ufile = open(tdir+'U', 'r') # open output velocity file

	# store velocity components into U 
	for line in ufile:
		if (line.startswith('internalField')):
			N = int(next(ufile).strip()) # get number of volumes 
			# skip line 
			next(ufile)

			U = np.zeros((N,3)) # store Ux, Uy, Uz 
			i = 0 # store line number 
			for line in ufile: 
				if (line.strip() == ')'): # break if end of internalField output 
					break 

				# get velocity vector 
				U[i,:] = line[1:-2].split() # remove ( and ), split three components 

				i += 1 # update array location 

	ufile.close() # close velocity file 


	# --- get position --- 
	files = ['ccx', 'ccy', 'ccz'] # name of cell center files in 0 dir 

	# make sure files exist 
	if (not(os.path.isfile(initDir+files[0]))):
		os.system('writeCellCentres')

	r = np.zeros((N,len(files))) # stores position vector 

	for i in range(len(files)): # loop through cell center files 
		g = open(initDir+files[i], 'r') # open file i 
		for line in g: # loop through 
			if (line.startswith('internalField')): # skip until internalField 
				n = int(next(g).strip()) # get number of volumes 
				next(g) # skip line 

				assert (n == N) # make sure sizes same 

				j = 0 # array storage location 
				for line in g:
					if (line.strip() == ')'): # break if end of internalField 
						break 

					# get coordinate 
					r[j,i] = float(line.strip()) # store location 

					j += 1 # update array location 
		g.close()


	# --- get k --- 
	kfile = open(tdir+'k', 'r') # open output velocity file
	for line in kfile:
		if (line.startswith('internalField')):
			N = int(next(kfile).strip()) # get number of volumes 
			assert (N == n) # assert number of volume = same as from position file 

			# skip line 
			next(kfile)

			# store k 
			k = np.zeros(N) 

			i = 0
			for line in kfile:
				if (line.strip() == ')'): # break if end of internalField 
					break 

				# get k value 
				k[i] = float(line.strip()) 

				i += 1 # update array location 

	kfile.close() # close kfile 


	# --- get C --- 
	cfile = open(tdir + 'alpha.upper', 'r') # open concentration file 
	for line in cfile:
		if (line.startswith('internalField')):
			n = int(next(cfile).strip()) # get number of volumes 
			assert (n == N) # assert number of volumes same as k 

			# skip line 
			next(cfile)

			# store C
			C = np.zeros(n) 

			i = 0
			for line in cfile:
				if (line.strip() == ')'): # break if end of internal field 
					break 

				# get C values 
				C[i] = float(line.strip())

				i += 1 # update array location 

	cfile.close() # close c file 


	# --- interpolate to xinterp --- 
	y1, uinterp = interpolate(xinterp, r, U[:,0]) # get Ux profile 
	y1, kinterp = interpolate(xinterp, r, k) # get k profile 
	y1, Cinterp = interpolate(xinterp, r, C) # get concentration profile 

	if (PLOT):
		plt.plot(y1*1000, Cinterp)
		plt.xlabel('y (mm)')
		plt.ylabel('Ux (m/s)')
		plt.title(str(xinterp))
		plt.show()

	# write to file 
	# if (not(os.path.isdir('misc'))):
	# 	os.makedirs('misc') 
		
	# f = open('misc/readFoam_' + str(xinterp) + '.txt', 'w')
	# for i in range(len(y1)):
	# 	f.write(str(y1[i]) + ' ' + str(uinterp[i]) + ' \n')

	# f.close()

	return y1, uinterp, kinterp, Cinterp  

def readExperiment(case, dist):
	''' read in experimental data for location dist ''' 
	field = ['_PIV_', '_LIF_'] # velocity/k v concentration 
	if (case == 2):
		pre = 'N320/'
		post = 'dr1_u06.dat'
	elif (case == 1):
		pre = 'N337/'
		post = 'dr0_u10.dat'
	elif (case == 0):
		pre = 'N339/'
		post = 'dr0_u06.dat'

	pre = 'data/' + pre + 'X'

	# y, Vx, U_x95, k, kLow, kUp, x
	df = np.loadtxt(pre+dist+field[0]+post, skiprows=5, usecols=(1,2,3,15,16,17,0)) 

	y_ex = df[:,0] # y grid points 
	u_ex = -df[:,1] # Ux profile 
	sigma_ex = df[:,2] # 2 sigma uncertainty in Ux   
	k = df[:,3]
	kLow = df[:,4]
	kUp = df[:,5] 

	# get maximum uncertainty 
	ksigma = np.zeros(len(k))
	for i in range(len(ksigma)):
		# ksigma[i] = max(kLow[i], kUp[i]) # use larger of 2, 2 sigma 
		ksigma[i] = (kUp[i] - kLow[i])/2

	# y, c, c95 
	cf = np.loadtxt(pre+dist+field[1]+post, skiprows=3, usecols=(0,1,2))

	y_c = cf[:,0] # y points for concentration 
	c = cf[:,1] # concentration values 
	sigmac = cf[:,2] # 2 sigma uncertainty  

	x = -df[0,-1]/1000 # x location of experimental sensor, given as negative in mm 

	return y_ex, u_ex, sigma_ex, k, ksigma, y_c, c, sigmac, x

def compare(grid_ex, val_ex, grid, val):
	interp = np.interp(grid_ex, grid, val)

	norm = np.linalg.norm(val_ex - interp, 2)

	return norm 

if __name__ == '__main__':
	import matplotlib.pyplot as plt 

	import sys 

	dr = 'output/'

	subDirs = sorted(os.listdir(dr)) # get list of subdirectories in output

	fig1 = plt.figure()
	fig2 = plt.figure()
	fig3 = plt.figure()
	for i in range(len(subDirs)):
		cd = dr + subDirs[i] # current directory 

		uf = np.loadtxt(cd+'/U')
		kf = np.loadtxt(cd+'/k')
		cf = np.loadtxt(cd+'/C')

		ax1 = fig1.add_subplot(np.ceil(len(subDirs)/2), 2, i+1)
		ax1.plot(uf[:,0], uf[:,1])
		
		ax2 = fig2.add_subplot(np.ceil(len(subDirs)/2), 2, i+1)
		ax2.plot(kf[:,0], kf[:,1])

		ax3 = fig3.add_subplot(np.ceil(len(subDirs)/2), 2, i+1)
		ax3.plot(cf[:,0], cf[:,1])
	
	plt.show()


	# case = 0
	# if (len(sys.argv) == 2):
	# 	case = int(sys.argv[1]) # get command line case 

	# dist = ['050', '150', '250', '350', '450'] # experimental distances
	# d = np.array([.053383118, .15, .25, .35, .45])

	# fig1 = plt.figure(figsize=(16,12))
	# fig2 = plt.figure(figsize=(16,12))
	# fig3 = plt.figure(figsize=(16,12))
	# for i in range(len(dist)):
	# 	# read in experimental data 
	# 	y_ex, u_ex, sigma_ex, k_ex, ksigma, y_c, c_ex, sigmac_ex, x = readExperiment(case, dist[i])

	# 	# get openfoam data 
	# 	y, u, k, C = parse(x) 

	# 	y *= 1000 # convert to mm 

	# 	# plot Ux 
	# 	ax1 = fig1.add_subplot(np.ceil(len(dist)/2), 2, i+1)
	# 	ax1.plot(y_ex, u_ex)
	# 	ax1.plot(y, u)
	# 	ax1.set_title(str(x) + ', ' + str(compare(y_ex, u_ex, y, u)))
	# 	ax1.set_xlim(y_ex[0], y_ex[-1])

	# 	# plot k 
	# 	ax2 = fig2.add_subplot(np.ceil(len(dist)/2), 2, i+1)
	# 	ax2.plot(y_ex, k_ex)
	# 	ax2.plot(y, k)
	# 	ax2.set_title(str(x) + ', ' + str(compare(y_ex, k_ex, y, k)))
	# 	ax2.set_xlim(y_ex[0], y_ex[-1])

	# 	# plot concentration 
	# 	ax3 = fig3.add_subplot(np.ceil(len(dist)/2), 2, i+1)
	# 	ax3.plot(y_c, c_ex)
	# 	ax3.plot(y, C)
	# 	ax3.set_title(str(x) + ', ' + str(compare(y_c, c_ex, y, C))) 
	# 	ax3.set_xlim(y_c[-1], y_c[0])


	# plt.show()



