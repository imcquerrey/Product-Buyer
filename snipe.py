import requests
from bs4 import BeautifulSoup
import re
import time
import sys


# Discord Webhook
webhook = 'webhook here'
# Roblox Cookie of logged in Account
coookie = 'cookie here'
# Username of Roblox Account
username = 'username here'
sessiont = requests.session()

# Pass in the login cookie to the site
sessiont.get('https://www.roblox.com')
sessiont.cookies[".ROBLOSECURITY"] = coookie
r = sessiont.get('https://www.roblox.com')


# Grab username of the logged in account
soup = BeautifulSoup(r.text, 'lxml')
tag = soup.find('meta', {'name': 'user-data'})

# Check if the logged in username is the correct username
try:
	userid = str(tag['data-name'])
	print(userid)
	if userid != username:
		print('WRONG NAME')
		sys.exit()
except TypeError:
	print('Invalid Cookie')
	sys.exit()



# ID of the product to purchase is given via args where it is then stored in here
productid = (sys.argv)[1]
print(productid)


session1 = requests.session()
sessionb = requests.session()

# Pass in the login cookie to the site for the new session
sessionb.get('https://www.roblox.com')
sessionb.cookies[".ROBLOSECURITY"] = coookie
r = sessionb.get('https://www.roblox.com')




# When getting product info some requests made to the apis can be denied so it will keep trying to get the product info
# until it is successful
while True:
	try:
		# Get product asset id and name through the roblox api
		r = session1.get('https://api.roblox.com/Marketplace/ProductDetails?productId=%s' % productid)
		assetid = str(r.json()['AssetId'])
		name = str(r.json()['Name'])

		# Get product average price through the api
		r = session1.get('https://www.roblox.com/asset/%s/sales-data' % assetid)
		priceavg = r.json()['data']['AveragePrice']

		# Get the cheapest rate of the product
		r = session1.get(
			'https://www.roblox.com/asset/resellers?productId=%s&startIndex=0&maxRows=1' % productid)
		inf = r.json()['data']['Resellers'][0]
		price = inf['Price']

		# Find out which one of the two prices is more
		if price < priceavg:
			price = priceavg

		# Using the item price the fee that items are taxed on is accounted for which is %30 of the price of the item sold
		buypri1 = price * .7
		# Then the new price with the tax accounted for is calculated with the buy percent which is .75 75%
		# With a buy price of 75% the program will only purchase the product when the the profit after selling back
		# the item at market value is 25% or above
		buypri = int(format(buypri1 * .75, ".0f"))
		print('Valid Product Id')
		break
	except Exception as e:
		if 'Max retries exceeded with url' in str(e):
			print('Max Tries Exceeded')
		else:
			print('Invalid Product Id')
		time.sleep(5)

# Make a get request to roblox so that the program can get the X-CSRF-TOKEN which is used when submiting forms or in
# this case, purchasing the product
r = sessionb.get('https://www.roblox.com/catalog/%s/' % assetid)
val = re.search('Roblox.XsrfToken.setToken', r.text)
val = val.span()[1] + 2
val2 = val + 12
tok = r.text[val:val2]
# It is then placed in headers along with the User-Agent
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0',
		   'X-CSRF-TOKEN': tok}

try:
	while True:
		try:
			# Getting the cheapest seller's price of the product the program is looking to buy
			r = session1.get(
				'https://www.roblox.com/asset/resellers?productId=%s&startIndex=0&maxRows=1' % productid)
			inf = r.json()['data']['Resellers'][0]
			price = inf['Price']
			# Check it against the buy price to make sure that there is enough profit being made
			if price <= buypri:
				# Gather additional info from the original request to get the price
				userassetid = inf['UserAssetId']
				sellerid = inf['SellerId']
				# Make the request to purchase the product
				r = sessionb.post('https://www.roblox.com/API/Item.ashx?rqtype=purchase&productID=%s&expectedCurrency=1&expectedPrice=%s&expectedSellerId=%s&userAssetID=%s' % (productid, price, sellerid, userassetid), headers=headers)
				fw = open('log_%s.txt' % productid, 'a')
				# If the status code of the request is 200 that means the request was received properly
				if r.status_code == 200:
					try:
						# If the request contains returned json data that usually means the product wasn't purchased for
						# some reason so its then checked against known errors then logged to the text file
						fw.write(str(r.json()) + '\n')
						if r.json()['errorMsg'] == 'This item is not for sale.':
							fw.write('Someone else purchased the item: %s for: %s\n' % (assetid, price))
							fw.write(str(r.status_code) + '\n')
							fw.write('---------------------------------------\n')
							fw.close()
						elif r.json()['showDivID'] == 'InsufficientFundsView':
							fw.write('Not Enough Funds to purchase %s for %s\n' % (assetid, price))
							fw.write('---------------------------------------\n')
							fw.close()
						else:
							fw.write('ELSE\n')
							fw.write(str(r.json()) + '\n')
							fw.write('---------------------------------------\n')
							fw.close()
					except:
						# The error that would occur would be there being no json to check error messages from meaning
						# that the purchase was successful. Then it is logged to then text file
						fw.write('Purchased Item for: %s\n' % price)
						fw.write('---------------------------------------\n')
						fw.close()
						# This request is used to grab the product's image
						r = session1.get('https://www.roblox.com/catalog/%s/' % assetid)
						url = str(r.url)
						soup = BeautifulSoup(r.text, 'lxml')
						tag = soup.find_all('span', {'class': 'thumbnail-span'})[0]
						pic = str(tag.find('img')['src'])

						# The payload for the discord webhook is then constructed with the item name, picture, price bought
						# and the person who bought it
						# The use of the discord webhook is to alert the user that the program has purchase a product
						payload = {'username': 'Sniper', 'avatar_url': 'https://vgy.me/tOfCm5.png', 'embeds': [{
						"title": "Sniper: Item Sniped! By: Owner",
						"description": "Purchased **%s** for **%sR$**\n%s" % (
						name, price, url),
						"thumbnail": {
							"url": pic
						},

						}]}
						r = requests.post(webhook, json=payload)
				else:
					# If the html code is not 200 it is either a 400 code meaning the request was not received properly
					# which can happen with the speed and amount of requests constantly being made
					# If it is a 403 error that means roblox has denied the request due to too many requests being made
					fw.write('Failed to purchase item: %s for %s\n' % (assetid, price))
					fw.write(str(r.status_code) + '\n')

					if r.status_code == '403':
						# To fix this error from happening again when the loop finishes the session is re-initialized
						fw.write('403 Error\n')
						sessionb = requests.session()

						# Pass in the login cookie to the site and a new X-CSRF-TOKEN is collected again
						sessionb.get('https://www.roblox.com')
						sessionb.cookies[".ROBLOSECURITY"] = coookie
						r = sessionb.get('https://www.roblox.com/catalog/%s/' % assetid)
						val = re.search('Roblox.XsrfToken.setToken', r.text)
						val = val.span()[1] + 2
						val2 = val + 12
						tok = r.text[val:val2]
						headers = {
							'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0',
							'X-CSRF-TOKEN': tok}
						fw.write('Refresh\n')
					try:
						fw.write(str(r.json()) + '\n')
					except:
						pass
					fw.write('---------------------------------------\n')
					fw.close()

		except Exception as e:
			# If an error occurs here it is most likely due to the site blocking the get or post request
			# in which the sessions are re-initialized
			session1 = requests.session()
			sessionb = requests.session()

			# Pass in the login cookie to the site
			sessionb.get('https://www.roblox.com')
			sessionb.cookies[".ROBLOSECURITY"] = coookie
			r = sessionb.get('https://www.roblox.com/catalog/%s/' % assetid)
			val = re.search('Roblox.XsrfToken.setToken', r.text)
			val = val.span()[1] + 2
			val2 = val + 12
			tok = r.text[val:val2]
			headers = {
				'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0',
				'X-CSRF-TOKEN': tok}


except Exception as e:
	# Error handling logged to text file
	fw = open('log_%s.txt' % productid, 'a')
	fw.write('Error\n')
	fw.write(str(e) + '\n')
	fw.close()
	sys.exit()


