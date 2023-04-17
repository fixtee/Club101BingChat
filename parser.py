import requests
from bs4 import BeautifulSoup
import article_parser
import newspaper
import urllib.parse

def url_article_parser(url: str, parser_option: int = 1, orig_url: bool = False) -> str:

  if not orig_url:
    url = f'https://readability-bot.vercel.app/api/readability?url={urllib.parse.quote(url, safe="")}'
      
  if parser_option == 1: # Parser 1
    article = newspaper.Article(url=url)
    article.download()
    article.parse()
    content = article.text
  elif parser_option == 2: # Parser 2
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    article = soup.find('article')
    content = article.text
  elif parser_option == 3: # Parser 3
    title, content = article_parser.parse(url=url, output='markdown', timeout=5)
  else:
    raise ValueError("Invalid parser option. Please select 1, 2 or 3.")
  
  return content

def get_parser_params(text: str) -> dict:
  parser_option = 1
  orig_url = False

  parser_option_index = text.find('paropt')
  if parser_option_index != -1:
      start_ind = parser_option_index + len('paropt')
      paropt = text[start_ind: start_ind+2]
  else:
      paropt = ''

  if paropt != '':
    try:
      parser_option = int(paropt[0])
      if paropt[1] == '1':
        orig_url = True
    except (ValueError, IndexError):
      # ignore non-integer line numbers or out-of-range index
      pass

  return {'parser_option': parser_option, 'orig_url': orig_url}
