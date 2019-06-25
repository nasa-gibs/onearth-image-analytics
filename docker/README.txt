The Dockerfiles in this repository require OnEarth 2.0.0 or greater to be running. 
OnEarth creates a Docker network which this image uses to request image files. Moreover,
the server must be configured to serve images locally from the WMTS endpoint. See the notes
on configuring OnEarth to run locally.

For quick demonstrations, you can change the url from localhost to the online GIBS server
URL. This will hurt performance compared to running it locally, but will work for demonstrations.
