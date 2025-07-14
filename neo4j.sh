# start neo4j server
docker run --name neo4j-apoc -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/your_password -e NEO4J_apoc_export_file_enabled=true -e NEO4J_apoc_import_file_enabled=true -e NEO4J_apoc_import_file_use__neo4j__config=true -e NEO4JLABS_PLUGINS='["apoc"]' --user $(id -u):$(id -g) -v $(pwd)/neo4j.conf:/conf/neo4j.conf -v $(pwd)/output:/var/lib/neo4j/import -v $PWD/data:/data -v $PWD/plugins:/plugins neo4j:4.4 2>&1 | tee neo4j_docker.log

# create ssh tunnel to view database from desktop 
ssh -NfL localhost:7474:localhost:7474 -L localhost:7687:localhost:7687 manar@scale04.engin.brown.edu

# create ssh tunnel to view database from desktop 
ssh -NfL 5432:localhost:5432  manar@scale04.engin.brown.edu