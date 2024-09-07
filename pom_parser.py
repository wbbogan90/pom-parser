from xml.etree import ElementTree
import requests

MAVEN_CENTRAL_BASE = 'https://repo.maven.apache.org/maven2'
MAVEN_XMLNS = {'xmlns' : 'http://maven.apache.org/POM/4.0.0'}

def get_pom_file(coordinates:str) -> str:
    parts = coordinates.split(':')
    org_id = parts[0]
    artifact_id = parts[1]
    version = parts[2]
    pom_url = f"{MAVEN_CENTRAL_BASE}/{org_id.replace('.','/')}/{artifact_id}/{version}/{artifact_id}-{version}.pom"
    pom_content = requests.get(pom_url, stream=True).content.decode('utf-8')
    return pom_content

if __name__ == '__main__':
    pom_data = get_pom_file("io.quarkus:quarkus-bom:3.13.3")
    
    pass
