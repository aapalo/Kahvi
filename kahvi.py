#!/usr/bin/python
''' paivitetty: aapalo, 2.7.2015

huomioitavaa siirtaessa toiselle koneelle: 
 * sudo apt-get install python-serial
 * oikea portti ttyUSB0 vai ttyUSB1
 * tallennusosoite oikein
 * katso etta DEVAUS = 0
'''

import serial
import time as ti
import datetime
import zmq
import os

DEVAUS = 0

'''
try:
	context = zmq.Context()
	socket = context.socket(zmq.PUB)
	socket.connect("tcp://s-mikro-66:22222")
except:
	print 'oispa palvelin'
'''

portti = '/dev/ttyUSB0'
tallennusosoite = '/root/paja/kahvi/kahvidata.csv' #iso filu, kaikki data
pikkuosoite = '/root/paja/kahvi/nyt.txt' #pieni filu, vain nykydata
taysi_osoite = '/root/paja/kahvi/taysi.txt' #milloin kahvi keitetty
taysi_osoite2 = '/root/paja/kahvi/taysi_backup.txt' #milloin kahvi keitetty, luetaan ekalla kierroksella
sleeptime = 0 #viive sekunteina

i = 0
j = 0

lisaviive = 0

while 1:
        today = datetime.date.today()
        currentTime = today.strftime('%m/%d/%Y ') + datetime.datetime.now().strftime("%H:%M:%S")
        currentTime2 = datetime.datetime.now().strftime("%H:%M")
	#eka kierros
	if (i == 0):
		
		with open(taysi_osoite2, 'r') as fkirj3:
	       		viimeaika = fkirj3.readline().strip('\n')
       			keittoaika = fkirj3.readline().strip('\n')
		pannutieto = 'Kahvi keitetty ' + keittoaika
		print pannutieto
		if(DEVAUS):
			print viimeaika, keittoaika
		#viimeaika = currentTime
		pvaerotus = 0
		tuntierotus = 0
		minuuttierotus = 0
		keittoaika = '00:07'
		status = 0 #1 tays, 2 puol, 3 tippa, 4 tyhj, 5 tippuu
		csv_lahetetty = 0
		tiedostot_lahetetty = 0

        aika = (int(datetime.datetime.now().strftime("%H"))*60 + int(datetime.datetime.now().strftime("%M")))
	#Onko laite usb-portissa
	try:
		ser = serial.Serial(portti, baudrate=9600, timeout=4, rtscts=0, dsrdtr=0)
	except (serial.SerialException, OSError):
		print 'Laite irti'
		ti.sleep(60)
		continue
	if(0):
		i = 1
	else:	#onko esim uploadaus menossa
		try:
			asd = ser.readline().strip()
		except (serial.SerialException, OSError):
			print 'oispa input'
			ti.sleep(10)
			continue
		lampo = (asd.split(',')[0])

	try:
		lampo = float(lampo)
	except ValueError:
		print 'hups: ' + lampo
		ti.sleep(5)
		continue
	#tsekkaa onko fiksu arvo
	if ((lampo > 15.0) and (lampo < 150.0)):
		savestr = currentTime + ',' + asd
	else:
		ti.sleep(5)
		continue
	'''
	try:
		socket.send('COFFEETEMP,' + str(asd))
	except:
		print 'oispa soketti'
	'''

	if (j > (4+lisaviive)):
		j = 0
		#tallenna uusin rivi, lisaa filun loppuun
		with open(tallennusosoite, 'ab') as fkirj:
			fkirj.write(savestr + '\n')
		print savestr
	if (j == 0):
		with open(pikkuosoite, 'w') as fkirj2:
       	       		fkirj2.write(savestr)
	if (aika % 5 == 0): #5min valein
		if (csv_lahetetty == 0):
			#os.system('cat /root/paja/kahvi/kahvidata.csv | ssh kahvi@sika "cat >> /home/kahvi/kahvidata.csv"')
			#os.system('scp "%s" "kahvi@sika:"' % (tallennusosoite))
			os.system('rsync --append "%s" "kahvi@sika:"' % (tallennusosoite))
			os.system('ssh kahvi@sika "tail -n 5000 kahvidata.csv > kahvidatatail.csv"')
			csv_lahetetty = 1
	else:
		csv_lahetetty = 0

	#2min valein
	if (aika % 2 == 0):
		if (j == 1):
			if(tiedostot_lahetetty == 0):
		       		os.system('scp "'+pikkuosoite+'" kahvi@sika:')
			       	os.system('scp "'+taysi_osoite+'" kahvi@sika:')
				tiedostot_lahetetty = 1
		status = int(asd.split(',')[1])
		if (status == 5):
			keittoaika = today.strftime('%d.%m.') + ' klo ' + datetime.datetime.now().strftime("%H:%M")
			keittoaika2 = datetime.datetime.now().strftime('%H:%M')
			viimeaika = currentTime
			with open(taysi_osoite2, 'w') as fkirj3:
	       	       		fkirj3.write(viimeaika +'\n'+ keittoaika)

		#pannutieto = 'Kahvi keitetty ' + keittoaika
		#nykyinen aika
		aikau1 = currentTime.split('/')
		aikau2 = aikau1[2].split()[1].split(':')
		aikau3 = int(aikau2[0])*60+int(aikau2[1])
		#viimeaika, uusin pannullinen
		aikav1 = viimeaika.split('/')
		aikav2 = aikav1[2].split()[1].split(':')
		aikav3 = int(aikav2[0])*60+int(aikav2[1])

		#status = 5 #(testailua varten)

		while(1):
			#pva
			pvaerotus = int(aikau1[1]) - int(aikav1[1])
			if (pvaerotus > 0):
				if (status < 4):
					if (pvaerotus == 1):
						pannutieto = 'Kahvi keitetty eilen. Kaada pois.'
						break
					else:
						pannutieto = 'Kahvi keitetty kauan sitten. Kaada pois.'
						break
			elif (pvaerotus < 0):
				pannutieto = 'Kahvi lienee vanhaa. Kaada pois.'
				break

			if(status == 1):
				pannutieto = 'Kahvia kokonainen pannu'
			if(status == 2):
				pannutieto = 'Kahvia puolikas pannullinen'
			if(status == 3):
				pannutieto = 'Kahvia tippa'
			if(status == 4):
				pannutieto = 'Ei kahvia :('
				break
			if(status == 5):
				pannutieto = 'Kahvi tippumassa :)'
				break
			if(status == 0):
				pannutieto = "Voipi olla kahvia, voipi olla olematta"
				break
			minuuttierotus = aikau3 - aikav3
			tuntierotus = minuuttierotus / 60
			if(minuuttierotus < 5):
				pannutieto += ', justiinsa keitetty'
				break
			if(minuuttierotus < 15):
				pannutieto += ', keitetty alle vartti sitten'
				break
			if(minuuttierotus < 30):
				pannutieto += ', keitetty alle puoli tuntia sitten'
				break
			if (minuuttierotus < 60):
				pannutieto += ', keitetty alle tunti sitten'
				break
			if (minuuttierotus < 120):
				pannutieto += ', keitetty alle kaksi tuntia sitten'
				break
			if (minuuttierotus < 180):
				pannutieto += ', keitetty alle kolme tuntia sitten'
				break
			if (minuuttierotus > 180):
				pannutieto = 'Kahvi keitetty monta tuntia sitten, lienee jo loppu'
				break
			break
	else:
		tiedostot_lahetetty = 0
	if (DEVAUS):
		'''
		print asd
		print lampo
	        print savestr
		print "%d %d" % (aika, lisaviive)
		print savestr.split(',')
		print 'asd.split: ' + asd.split(',')[1]
		print aikav1, aikau1
		print aikav2, aikau2
		print aikav3, aikau3
		print aikau2[1], aikav2[1]
		'''
		print str(pvaerotus) + ' ' + str(tuntierotus) + ' ' + str(minuuttierotus)
		print pannutieto

	with open(taysi_osoite, 'w') as ftays:
       		ftays.write(pannutieto + '\n')


	j += 1
        i += 1
	#klo 08-20 tiuhempi mittausvali
	if ((aika > 480) and (aika < 1200)):
		#harvempi mittausvali kun pannu ei paalla
		if (lampo < 30.0):
			lisaviive = 40
		else:
			lisaviive = 0
	else:
		lisaviive = 60
