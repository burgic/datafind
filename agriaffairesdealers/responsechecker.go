package main

import (
	"crypto/tls"
	"fmt"
	"io/ioutil"
	"log"
	"math/rand"
	"net/http"
	"time"
)

var rng = rand.New(rand.NewSource(time.Now().UnixNano()))

func createClient() *http.Client {
	transport := &http.Transport{
		TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
	}

	client := &http.Client{
		Timeout:   30 * time.Second,
		Transport: transport,
	}

	return client
}

func makeRequest(url string) (*http.Response, error) {
	client := createClient()
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, err
	}

	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
	req.Header.Set("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
	req.Header.Set("Accept-Language", "en-GB,en;q=0.5")

	req.Header.Set("X-Forwarded-For", "81.2.69.142") // An example UK IP address
	req.Header.Set("CF-IPCountry", "GB")

	req.AddCookie(&http.Cookie{Name: "country_code", Value: "gb"})

	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	return resp, nil
}

func randomDelay() {
	delay := rng.Intn(2) + 2 // Random delay between 2 to 4 seconds
	time.Sleep(time.Duration(delay) * time.Second)
}

func saveHTMLToFile(body []byte) error {
	filename := "response.html"
	err := ioutil.WriteFile(filename, body, 0644)
	if err != nil {
		return fmt.Errorf("error saving HTML to file: %v", err)
	}
	fmt.Printf("Full HTML response saved to %s\n", filename)
	return nil
}

func checkWebsite(url string) {
	log.Printf("Checking website: %s", url)
	randomDelay()

	resp, err := makeRequest(url)
	if err != nil {
		log.Fatalf("Error fetching the website: %v", err)
	}
	defer resp.Body.Close()

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		log.Fatalf("Error reading the response body: %v", err)
	}

	if err := saveHTMLToFile(body); err != nil {
		log.Printf("Warning: %v", err)
	}

	fmt.Printf("Status Code: %d\n", resp.StatusCode)
	fmt.Printf("Content Length: %d bytes\n", len(body))
	fmt.Printf("Response Headers:\n")
	for key, values := range resp.Header {
		for _, value := range values {
			fmt.Printf("%s: %s\n", key, value)
		}
	}
	fmt.Printf("\nFirst 1000 characters of the response body:\n%s\n", string(body[:min(1000, len(body))]))

	// Check for specific elements that should be present in a successful response
	if resp.StatusCode == 200 {
		if contains(body, []byte("listing-block listing-block--dealer")) {
			fmt.Println("\nThe response contains dealer listing blocks.")
		} else {
			fmt.Println("\nWARNING: The response does not contain dealer listing blocks.")
		}
		if contains(body, []byte("pagination--nav")) {
			fmt.Println("The response contains pagination elements.")
		} else {
			fmt.Println("WARNING: The response does not contain pagination elements.")
		}
	}
}

func contains(haystack, needle []byte) bool {
	return string(haystack[:min(len(haystack), len(needle))]) == string(needle)
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func main() {
	url := "https://www.agriaffaires.co.uk/pros/list/1-france.html"
	checkWebsite(url)
}