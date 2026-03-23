# Makefile for Weight Gurus project

# Default target
all: help

# Default image name
IMAGE ?= ghcr.io/faisalmemon/weightgurus

# Build Docker image (single arch)
.PHONY: docker

docker:
	@echo "Building Docker image..."
	docker build -t $(IMAGE) .

# Build local image with latest-local tag
.PHONY: docker-local

docker-local:
	@echo "Building local Docker image with tag $(IMAGE):latest-local..."
	docker build -t $(IMAGE):latest-local .

# Common target to ensure a buildx builder exists
.PHONY: ensure-buildx
ensure-buildx:
	@docker buildx ls | grep -q "weightgurus-builder" || docker buildx create --name weightgurus-builder --driver docker-container --use

# Build multi-arch image (pushes to registry)
.PHONY: docker-multi

docker-multi: ensure-buildx
	@echo "Building multi-arch Docker image and pushing..."
	docker buildx build --platform linux/amd64,linux/arm64 -t $(IMAGE):latest --push .

# Build multi-arch image locally without pushing
.PHONY: docker-multi-local

docker-multi-local: ensure-buildx
	@echo "Building multi-arch Docker image locally..."
	docker buildx build --platform linux/amd64,linux/arm64 -t $(IMAGE):latest --load .

# Clean Docker image (optional)
.PHONY: clean-docker
clean-docker:
	@echo "Removing Docker image weightgurus..."
	docker rmi weightgurus || true

# Help
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  docker            – Build Docker image (single arch)"
	@echo "  docker-local      – Build local image with latest-local tag"
	@echo "  docker-multi       – Build multi-arch image and push to registry"
	@echo "  docker-multi-local – Build multi-arch image locally (no push)"
	@echo "  clean-docker      – Remove the Docker image"
	@echo "  help              – Show this help"
