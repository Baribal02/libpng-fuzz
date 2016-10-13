// Copyright 2016 Google Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
////////////////////////////////////////////////////////////////////////////////

def call(body) {
    // evaluate the body block, and collect configuration into the object
    def config = [:]
    body.resolveStrategy = Closure.DELEGATE_FIRST
    body.delegate = config
    body()

    // Mandatory configuration
    def gitUrl = config["git"]
    assert gitUrl : "git should be specified"

    // Optional configuration
    def projectName = config["name"] ?: env.JOB_BASE_NAME
    def dockerfile = config["dockerfile"] ?: "oss-fuzz/$projectName/Dockerfile"
    def sanitizers = config["sanitizers"] ?: ["address"]
    def checkoutDir = config["checkoutDir"] ?: projectName
    def dockerContextDir = config["dockerContextDir"]

    def date = java.time.format.DateTimeFormatter.ofPattern("yyyyMMddHHmm")
        .format(java.time.LocalDateTime.now())

    node {
      def workspace = pwd()
      def revisionsFile = "$workspace/${projectName}.rev"
      def dockerTag = "ossfuzz/$projectName"
      echo "Building $dockerTag"

      // rm files with docker first to use the same user
      sh "docker run --rm -v $workspace/out:/out ubuntu /bin/sh -c 'rm -rvf /out/*'"
      sh "rm -rf $workspace/out"
      sh "mkdir -p $workspace/out"

      stage("docker image") {
          def revisions = [:]
          dir('oss-fuzz') {
              git url: "https://github.com/google/oss-fuzz.git"
          }

          dir(checkoutDir) {
              git url: gitUrl
              revisions[gitUrl] = sh(returnStdout: true, script: 'git rev-parse HEAD').trim()
          }

          if (dockerContextDir == null) {
            dockerContextDir = new File(dockerfile)
                .getParentFile()
                .getPath();
          }

          sh "docker build -t $dockerTag -f $dockerfile $dockerContextDir"

          def revText = groovy.json.JsonOutput.toJson(revisions)
          writeFile file: revisionsFile, text: revText
          echo "revisions: $revText"
      }
        
      for (int i = 0; i < sanitizers.size(); i++) {
        def sanitizer = sanitizers[i]
        dir(sanitizer) {
          def out = "$workspace/out/$sanitizer"
          sh "mkdir $out"
          stage("$sanitizer sanitizer") {
            // Run image to produce fuzzers
            sh "docker run -v $workspace/$checkoutDir:/src/$checkoutDir -v $out:/out -e SANITIZER_FLAGS=\"-fsanitize=$sanitizer\" -t $dockerTag"
          }
        }
      }

      // Run each of resulting fuzzers.
      stage("running fuzzers") {
        def resultsDir = "$workspace/test-results"
        sh "rm -rf $resultsDir"
        sh "mkdir -p $resultsDir"
        dir ('out') {
          def fuzzersFound = 0
          sh "ls -alR"
          for (int i = 0; i < sanitizers.size(); i++) {
            def sanitizer = sanitizers[i]
            dir (sanitizer) {               
              def d = pwd()
              def files = findFiles()
              for (int j = 0; j < files.size(); j++) {
                def file = files[j]
                if (file.directory) { continue }
                if (!new File(d, file.name).canExecute()) {
                    echo "skipping: $file"
                    continue
                }
                sh "docker run --rm -v $d:/out -t ossfuzz/libfuzzer-runner /out/$file -runs=32"
                fuzzersFound += 1
              }
                
              def testReport = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" + 
                    "<testsuites xmlns=\"http://junit.org/junit4/\"\n" +
                    "            xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"\n" +
                    "            xsi:schemaLocation=\"http://junit.org/junit4/ http://windyroad.com.au/dl/Open%20Source/JUnit.xsd\">\n" +
                    "    <testsuite name=\"expat-address\"\n" +
                    "               errors=\"0\"\n" +
                    "               failures=\"0\"\n" +
                    "               hostname=\"localhost\"\n" +
                    "               id=\"test\"\n" +
                    "               package=\"$projectName\"\n" +
                    "               tests=\"1\"\n" +
                    "               time=\"1s\"\n" +
                    "               timestamp=\"0\">\n" +
                    "         <testcase name=\"aName\" classname=\"aClassName\" time=\"1s\"/>\n" +
                    "    </testsuite>\n" +
                    "</testsuites>\n";
              writeFile file:"$resultsDir/TEST-${sanitizer}.xml", text:testReport
              sh "cat $resultsDir/TEST-${sanitizer}.xml"
            }
          }
          // sh "ls -al $resultsDir/"
          // step([$class: 'JUnitResultArchiver', testResults: '**/TEST-*.xml'])
          echo "Tested $fuzzersFound fuzzer"
          if (!fuzzersFound) {
            error "no fuzzers found";
          }
        }

        stage("uploading") {
            dir('out') {
              for (int i = 0; i < sanitizers.size(); i++) {
                def sanitizer = sanitizers[i]
                dir (sanitizer) {
                  def zipFile = "$projectName-$sanitizer-${date}.zip"
                  def revFile = "$projectName-$sanitizer-${date}.rev"
                  sh "cp $revisionsFile $revFile"
                  sh "zip -j $zipFile *"
                  sh "gsutil cp $zipFile gs://clusterfuzz-builds/$projectName/"
                  sh "gsutil cp $revFile gs://clusterfuzz-builds/$projectName/"
                }
             }
          }
        }

        stage("pushing image") {
          docker.withRegistry('', 'docker-login') {
            docker.image(dockerTag).push()
          }
        }
      }
    }

  echo 'Done'
}

return this;
