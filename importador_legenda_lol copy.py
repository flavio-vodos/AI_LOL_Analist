#utilizado a biblioteca gdown, pois o wget não consegue acessar arquivos em google drive.

import gdown

url = "https://drive.google.com/uc?id=1ecAYTTaPArL0m1NXDFPtSXl2LNNfX6dq"
output = "legenda_abreviaturas_lol.csv"
gdown.download(url, output, quiet=False)