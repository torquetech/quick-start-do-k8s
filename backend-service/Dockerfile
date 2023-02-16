FROM --platform=linux/x86_64 golang:1.18 AS build

WORKDIR /build
COPY go.mod go.sum /build/

RUN go mod download && \
    go mod verify

COPY . /build/
RUN go build ./...

FROM --platform=linux/x86_64 golang:1.18

COPY --from=build /build/app /usr/local/bin/

CMD ["app"]
