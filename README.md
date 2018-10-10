# tp1-distribuidos1

Esta es la resolución del TP 1 de la materia Sistemas Distribuidos 1.

Es la implementación de un server de JSONs a través de HTTP.
Los JSONs deben poder ser distribuidos en una cantidad arbitraria de servers auxiliares.



## Como ejecutar?


> sh run.sh $NUMERO_DE_FILESERVERS



## Como correr las pruebas?

### Cache


NO Teniendo la app corriendo, ejecutar:

> sh src/cache_test.sh

### Otras pruebas

Teniendo la app corriendo, ejecutar:

> python3 src/general_tests.py
> python3 src/general_tests.py
> python3 src/general_tests.py


# Limpiar archivos y logs creados.

> sh clean.sh