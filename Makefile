.PHONY: ci-build ci-run ci-test ci-remove ci-clean ci-push-tag ci-push-latest ci-login

NAME   := os-conductor
ORG    := openspending
REPO   := ${ORG}/${NAME}
TAG    := $(shell git log -1 --pretty=format:"%h")
IMG    := ${REPO}:${TAG}
LATEST := ${REPO}:latest

ci-build:
	docker pull ${LATEST}
	docker build --cache-from ${LATEST} -t ${IMG} -t ${LATEST} .

ci-run:
	docker-compose -f docker-compose.ci.yml up -d

ci-test:
	docker ps | grep os-conductor

ci-remove:
	docker rm -f ${NAME}

ci-clean:
	git stash --all

ci-push: ci-clean ci-build ci-login
	docker push ${IMG}
	docker push ${LATEST}

ci-push-tag: ci-clean ci-login
	docker build -t ${REPO}:${TAG} .
	docker push ${REPO}:${TAG}

ci-login:
	docker login -u ${DOCKER_USERNAME} -p ${DOCKER_PASSWORD}
