from xml.etree import ElementTree
import subprocess, os
import requests

MAVEN_CENTRAL_BASE = 'https://repo.maven.apache.org/maven2'
MAVEN_XMLNS = {'xmlns' : 'http://maven.apache.org/POM/4.0.0'}

def get_coordinates_from_url(maven_url:str):
    coordinates = ""
    if maven_url.startswith(MAVEN_CENTRAL_BASE):
        offset = len(MAVEN_CENTRAL_BASE) + 1
        paths = maven_url[offset:].split("/")
        paths.pop()
        version = paths.pop()
        artifact = paths.pop()
        group = ".".join(paths)
        coordinates = f"{group}:{artifact}:{version}"
    return coordinates    

def get_pom_files(coordinates:str) -> str:
    echo = subprocess.Popen(('echo', coordinates), stdout=subprocess.PIPE)
    pom_file_urls = subprocess.check_output('./go-maven-resolver', stdin=echo.stdout).decode('utf-8').split('\n')
    pom_files = {}
    for url in pom_file_urls:
        if url.startswith(MAVEN_CENTRAL_BASE):
            coordinates = get_coordinates_from_url(url)
            pom_files[coordinates] = url
    return pom_files

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
                dep_version = dependency.find("xmlns:version", namespaces=MAVEN_XMLNS)
                if not dep_version:
                    dep_version = version
                elif dep_version.text.startswith("${"):
                    version_ref = dep_version.text.lstrip('${').rstrip('}')
                    dep_version = properties[version_ref]
                else:
                    dep_version = dep_version.text
                dependencies.append(f"{groupId}:{artifactId}:{dep_version}")
    return list(set(dependencies))

if __name__ == '__main__':
    version = '0.45.0'
    pom_files:dict = get_pom_files(f"io.fabric8:docker-maven-plugin:{version}")
    dependencies = {}
    for key in pom_files.keys():
        pom_content = requests.get(pom_files[key], stream=True).content.decode('utf-8')
        pom_version = key.split(':')[2]
        pom_dependencies = get_dependencies(pom_xml_str=pom_content, version=pom_version)
        for pom_dep in pom_dependencies:
            dependencies[pom_dep] = "dependency"
    merged_dependencies = pom_files | dependencies
    with open('dependencies.txt', 'w') as dep_file:
        for dep in merged_dependencies.keys():
            dep_file.write(f"{dep}\n")

