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

def get_dependencies(pom_xml_str:str, version:str):
    root = ElementTree.fromstring(pom_xml_str)
    properties = {}
    properties['project.version'] = version
    dependencies = []
    # Extract the properties to get the version of any dependency that 
    # references a property
    for prop in root.findall('xmlns:properties', namespaces=MAVEN_XMLNS):
        for child in prop:
            if child.tag.startswith("{"):
                child.tag = child.tag.split('}', 1)[1]
            properties[child.tag] = child.text
    for deps in root.findall('xmlns:dependencies', namespaces=MAVEN_XMLNS):
        for dependency in deps.findall('xmlns:dependency', namespaces=MAVEN_XMLNS):
            scope = dependency.find("xmlns:scope", namespaces=MAVEN_XMLNS)
            do_include = True
            if scope != None:
                if scope.text not in ['compile','provided','runtime','system']:
                    do_include = False
            if do_include:
                groupId:str = dependency.find("xmlns:groupId", namespaces=MAVEN_XMLNS).text
                artifactId:str = dependency.find("xmlns:artifactId", namespaces=MAVEN_XMLNS).text
                dep_version:str = dependency.find("xmlns:version", namespaces=MAVEN_XMLNS).text
                if dep_version.startswith("${"):
                    version_ref = dep_version.lstrip('${').rstrip('}')
                    dep_version = properties[version_ref]
                dependencies.append(f"{groupId}:{artifactId}:{dep_version}")
    return list(set(dependencies))

if __name__ == '__main__':
    version = '0.45.0'
    pom_data = get_pom_file(f"io.fabric8:docker-maven-plugin:{version}")
    deps = get_dependencies(pom_xml_str=pom_data, version=version)
    for dep in deps:
        print(dep)

