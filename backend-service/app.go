package main

import (
	"database/sql"
	"fmt"
	"io"
	"net/http"
	"os"

	_ "github.com/lib/pq"
)

func getRoot(w http.ResponseWriter, r *http.Request) {
	connStr := os.Getenv("DB")
	db, err := sql.Open("postgres", connStr)
	if err != nil {
		fmt.Printf("error %s", err)
	}

	var time string
	row := db.QueryRow("SELECT NOW() AS time;")
	switch err := row.Scan(&time); err {
		case sql.ErrNoRows:
			fmt.Println("No rows were returned!")
		case nil:
			message := fmt.Sprintf("Database time: %s", time)
			io.WriteString(w, message)
		default:
			fmt.Println("Unknown Database error.")
			panic(err)
	}
}

func main() {
	http.HandleFunc("/backend-service", getRoot)

	err := http.ListenAndServe(":80", nil)
	if err != nil {
		fmt.Printf("error starting server: %s\n", err)
		os.Exit(1)
	}
}
