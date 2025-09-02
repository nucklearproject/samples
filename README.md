server.py recrea strudel.js y levanta el servidor http://localhost:5432/ 
Si se hace algun cambio en la carpeta(agregar nuevos samples, etc) hacemos un rebuild http://localhost:5432/rebuild desde el navegador no es necesario reiniciar el server. 

strudel.py Simplemente genera el strudel.json para ser llamado desde mi repositorio github, es util a menos que quieras clonar el repositorio y crear tu propio repositorio de samples. Solo debes cambiar la URL base.
Si deseas usarlo solo llama a la rama principal, o dependiendo si hay otras ramas 
samples('github:nucklearproject/samples/master')



