NUMBER_OF_FILESERVERS=1

echo "RESPONSES_PORT=8090
NUMBER_OF_FILESERVERS=$NUMBER_OF_FILESERVERS
VERBOSITY=4
CACHE_CAPACITY=0" > docker-variables.env

docker-compose up --build --scale file=$NUMBER_OF_FILESERVERS -d &&
echo "---- Without cache -----" &&
python3 src/lots_of_gets.py &&
docker-compose stop &&

echo "RESPONSES_PORT=8090
NUMBER_OF_FILESERVERS=$NUMBER_OF_FILESERVERS
VERBOSITY=4
CACHE_CAPACITY=2250" > docker-variables.env && 

docker-compose up --build --scale file=$NUMBER_OF_FILESERVERS -d &&
echo "---- Without cache -----" &&
python3 src/lots_of_gets.py &&
docker-compose stop
