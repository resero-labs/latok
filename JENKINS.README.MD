Instructions for Setting Up Jenkins Build
-----------------------------------------

# Build Parameters
Setup the following Build Parameters

1) BUILD_IMAGE_NAME - Should be the name of the project with a `-jenkins` appended.
2) IMAGE_NAME - Should be the name of the ECS Repository & image name that the image will be published to.
3) BASE_IMAGE_NAME - Should be the name of the project with a `-prod` appended.

# Execute Shell

The build is a set of commands to be executed in a build shell

The commands follow:

```
# Remove previous build's images and containers
sudo docker rmi $(sudo docker images | grep $IMAGE_NAME | tr -s ' ' | cut -d ' ' -f 3) || true
sudo docker rmi $(sudo docker images | grep $BASE_IMAGE | tr -s ' ' | cut -d ' ' -f 3) || true
sudo docker rmi $(sudo docker images | grep $BUILD_IMAGE_NAME | tr -s ' ' | cut -d ' ' -f 3) || true
sudo docker rm -vf BUILD_IMAGE_NAME || true

sudo $(aws ecr get-login --region us-west-2)

BUILD_NUMBER=$(python -c "import versioneer; print(versioneer.get_versions()['version'].replace('+', '-'))")

# Since this is going to be another docker container that is being run alongside of the
#   jenkins container, you can't reference the jenkins disk location, it must reference
#   the host machine's disk locations.  So either you will need to create a link

#JENKINS_HOME=/home/ubuntu/jenkins_home
DOCKER_RUN="sudo docker run --rm -v $PWD:/src \
  -v /var/jenkins_home/pip.conf:/root/.pip/pip.conf \
  -v /var/jenkins_home/.pypirc:/root/.pypirc \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /usr/bin/docker:/usr/bin/docker \
  -v $PWD/.git:/workdir/.git \
  -e BUILD_NUMBER=$BUILD_NUMBER \
  -e LANISTA_IMAGE_NAME=$LANISTA_IMAGE_NAME \
  --name $BUILD_IMAGE_NAME $BUILD_IMAGE_NAME:$BUILD_NUMBER"

cp /var/jenkins_home/pip.conf $PWD/pip.conf
sudo /var/jenkins_home/bin/build-image -i $BASE_IMAGE_NAME base
sudo /var/jenkins_home/bin/build-image -i $BUILD_IMAGE_NAME -t $BUILD_NUMBER jenkins

$DOCKER_RUN ls

echo "\n\n*******************************************"
echo "*   Cleaning the repo"
echo "*******************************************"
$DOCKER_RUN bin/clean

echo "\n\n*******************************************"
echo "*   Running Tests"
echo "*******************************************"
$DOCKER_RUN bin/test

echo "\n\n*******************************************"
echo "*   Creating Artifacts"
echo "*******************************************"
$DOCKER_RUN bin/package

echo "\n\n*******************************************"
echo "*   Publishing Artifacts"
echo "*******************************************"
$DOCKER_RUN bin/publish

echo "\n\n*******************************************"
echo "*   Building Prod Image"
echo "*******************************************"
sudo /var/jenkins_home/bin/build-image lanista -i $IMAGE_NAME -t $BUILD_NUMBER


echo "\n\n*******************************************"
echo "*   Publishing Lanista Artifacts"
echo "*******************************************"
sudo IMAGE_NAME=$IMAGE_NAME BUILD_NUMBER=$BUILD_NUMBER /var/jenkins_home/bin/publish-image

echo $BUILD_NUMBER > VERSION
```

# Update Build Name
`Read from file`: VERSION