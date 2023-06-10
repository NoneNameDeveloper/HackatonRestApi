#!/bin/bash

if [ "$#" -lt 1 ]; then
  echo "Использование: $0 <номер бота> [local]"
  exit 1
fi

if [[ "$1" == "1" ]]; then
    export TELEGRAM_TOKEN="6109375437:AAHODAg-plWR30GEooQRJpHWMRxYUtQ4cSY"
elif [[ "$1" == "2" ]]; then
    export TELEGRAM_TOKEN="6142964859:AAHJKGySO9XmdZaPGrsgkibIHMdUWQQvpFQ"
elif [[ "$1" == "3" ]]; then
    export TELEGRAM_TOKEN="6282430068:AAG6fc1fs6xN153lQj6zBQrg5NmJoGnuNy4"
else
  echo "Invalid bot number. Must be 1, 2 or 3."
  exit 1
fi

if [[ "$2" == "local" ]]; then
    export TADA_API_BASE_URL="http://127.0.0.1:8095"
else
    export TADA_API_BASE_URL="http://greed.implario.net:8095"
fi

export TADA_API_COMPANY_TOKEN="vi_V0CvBsUsFNkSuZc1QXw"
python3 bot_aio.py
