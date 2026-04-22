#!/usr/bin/env bash
set -e
kubectl rollout undo deployment/aceest-fitness -n aceest
kubectl rollout status deployment/aceest-fitness -n aceest
