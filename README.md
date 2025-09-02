*---- LOCAL SERVER ----* 

server.py recrea strudel.js y levanta el servidor local http://localhost:5432/ 
///RECUERDA que solo vas a poder llamar al server local si estas usando strudel en tu maquina local como esta en este instructivo https://codeberg.org/uzu/strudel ////

Si se hace algun cambio en la carpeta(agregar nuevos samples(soporta wav flac ogg), etc) hacemos un rebuild http://localhost:5432/rebuild desde el navegador no es necesario reiniciar el server. 

*------ CONSTRUYENDO EL STRUDEL.JSON ------*

strudel.py Simplemente genera el strudel.json para ser llamado desde mi repositorio github, es util a menos que quieras clonar el repositorio y crear tu propio repositorio de samples. Solo debes cambiar la URL base.
Si deseas usarlo solo llama a la rama principal, o dependiendo si hay otras ramas 
samples('github:nucklearproject/samples/master')

Ejemplo:

samples('github:nucklearproject/samples/master')
s("PERC_per:3*4")

Tambien puedes llamaro 
s("per:3 per:2*3").bank("PERC").fast(4)

s("KICK_bd:1*4")

etc

Puedes llamar directamente al json, recuerda que el navegador cachea el json, podrias agregar ?v=1 etc al final de la url
samples('https://raw.githubusercontent.com/nucklearproject/samples/master/strudel.json')
s("PERC_per:3*4")

-******-
Recuerda que es un repositorio personal, pero podes usarlo libremente. No te olvides de visitar la carpeta examples. 

Puede que parezca que esta desordenado, pero es solo el inicio del repositorio, cuando disponga de mas tiempo voy a ir organizandolo mejor, pero por ahora es lo que hay 😉

Feliz Algorave! ☆*: .｡. o(≧▽≦)o .｡.:*☆


