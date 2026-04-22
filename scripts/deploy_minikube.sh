#!/usr/bin/env bash
set -e
IMAGE_REPO="${1:-YOUR_DOCKERHUB_USERNAME/aceest-fitness}"
IMAGE_TAG="${2:-latest}"
FULL_IMAGE="${IMAGE_REPO}:${IMAGE_TAG}"
kubectl apply -f k8s/base/namespace.yaml
sed "s|IMAGE_PLACEHOLDER|$FULL_IMAGE|g" k8s/base/deployment.yaml | kubectl apply -f -
kubectl apply -f k8s/base/service.yaml
kubectl rollout status deployment/aceest-fitness -n aceest
kubectl get all -n aceest
minikube service aceest-fitness-service -n aceest --url
