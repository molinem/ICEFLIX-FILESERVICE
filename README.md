# 💾 Iceflix - FileService 
El servicio de ficheros se encarga de enviar al usuario el fichero para que pueda visualizarlo. El servicio debe leer de un directorio en el disco duro, que será pasado al servicio a través de su configuración, los ficheros que serán compartidos.

🔹 <b>Link repositorio</b> -> https://github.com/molinem/ICEFLIX-FILESERVICE

***
# 🧩 Autor 
🔸 **Luis Molina Muñoz-Torrero** <br>
***

## Información Útil
- Nuestro servicio de ficheros se anuncia en `Announcements` cada <b>10 segundos</b>.
- Anunciamos nuestros ficheros en `FileAvailability` cada <b>20 segundos</b> (este tiempo ha sido elegido debido a que no se menciona exáctamente cuanto debería ser)
- Haciendo uso de setup.py se ha creado en la carpeta `dist` un archivo denominado `iceflix_file-0.1.tar.gz` para instalarlo usaremos el <br> siguiente comando -> `pip install dist/iceflix_file-0.1.tar.gz` <br>
***
## ¿Cómo lanzamos el servicio? ⚡️
- Primero hacemos uso del comando `pip install .` <br>

- Para lanzar el servicio ejecutaremos `./run_service` el cuál iniciará el servicio <b>FileService</b> con la configuración que se encuentra en el configs/fileservice.config. Por ello es necesario que previamente editemos ese fichero añadiendo el <b>IceStorm.TopicManager</b> que queramos.
***
## Descripción clases

### FileService
- `openFile((self, media_id, user_token, current=None)` ->  dado el identificador del medio devolverá un proxy al manejador del archivo (FileHandler), que permitirá descargarlo.
- `uploadFile(self, uploader, admin_token, current=None)` -> dado el token de administrador y un proxy para la subida del archivo, lo guardará en el directorio y devolverá su identificador
- `removeFile(self, media_id, admin_token, current=None)` -> dado un identificador y el token de administrador, borrará el archivo del directorio.

### FileHandler
- `receive(self, size, userToken, current=None)` -> recibe el número indicado de bytes del archivo, se comprueba el userToken.
- `close(self, userToken, current=None)` -> indica al servidor que el proxy para este fichero ya no va a ser usado y puede ser eliminado, se comprueba el userToken.

### FileUploader
- `receive(self, size, current=None)` -> recibe el número indicado de bytes del archivo
- `close(self, current=None)` -> indica al servidor que el proxy para este fichero ya no va a ser usado y puede ser eliminado

### Announcements
- `announce(self, service, service_id, current=None)` -> De forma constante comprueba los servicios  y actualiza la lista de servicios conocidos que no han sido añadidos con anterioridad.

***
##  💭 Requisitos extras 

> Utilización de la librería `logging` de Python de manera adecuada. ✅ <br>

> El proyecto es instalable con `pip install` (setup.py) ✅ <br>

> El código obtiene de media en `pylint` > 9.0 ✅ <br>

> DockerFile ✅
