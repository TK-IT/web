FROM node:8-alpine AS builder
WORKDIR /build
COPY package.json package-lock.json ./
RUN npm i
COPY . .
RUN ./node_modules/.bin/webpack --mode production
