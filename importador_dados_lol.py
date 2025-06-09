import gdown

url = "https://drive.google.com/uc?id=1v6LRphp2kYciU4SXp0PCjEMuev1bDejc"
output = "2025loesport_matchdata.csv"  # Arquivo do drive "OE public match data"
gdown.download(url, output, quiet=False)
