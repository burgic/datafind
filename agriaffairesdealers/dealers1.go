package main

import (
	"crypto/tls"
	"encoding/csv"
	"fmt"
	"log"
	"net/http"
	"math/rand"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/PuerkitoBio/goquery"
)

var rng = rand.New(rand.NewSource(time.Now().UnixNano()))

// Dealer struct to hold the scraped data
type Dealer struct {
	URL       string
	Name      string
	Location  string
	Brands    string
	AdsCount  string
	Addresses string
}

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
	delay := rng.Intn(2) + 2
	time.Sleep(time.Duration(delay) * time.Second)
}

func scrapeListing(url string) ([]*Dealer, bool, error) {
	log.Printf("Scraping listing page: %s", url)
	randomDelay()
	resp, err := makeRequest(url)
	if err != nil {
		return nil, false, fmt.Errorf("error fetching listing page: %v", err)
	}
	defer resp.Body.Close()

	doc, err := goquery.NewDocumentFromReader(resp.Body)
	if err != nil {
		return nil, false, fmt.Errorf("error parsing listing page: %v", err)
	}

	var dealers []*Dealer
	baseURL := "https://www.agriaffaires.co.uk"

	dealerBlocks := doc.Find(".listing-block.listing-block--dealer")
	log.Printf("Number of dealer blocks found: %d", dealerBlocks.Length())

	dealerBlocks.Each(func(i int, s *goquery.Selection) {
		dealer := &Dealer{}

		nameElement := s.Find(".listing-block__link")
		href, exists := nameElement.Attr("href")
		if exists {
			dealer.URL = baseURL + href
		}
		dealer.Name = strings.TrimSpace(nameElement.Find(".listing-block__title").Text())

		dealer.Location = strings.TrimSpace(s.Find(".listing-block__localisation").First().Text())
		dealer.Addresses = strings.TrimSpace(s.Find(".listing-block__adresses").Text())

		dealer.Brands = strings.TrimSpace(s.Find(".listing-block__brands strong").Text())
		dealer.AdsCount = strings.TrimSpace(s.Find(".listing-block__number").Text())

		log.Printf("Extracted dealer: %+v", dealer)

		dealers = append(dealers, dealer)
	})

	var hasNextPage bool
	doc.Find(".pagination--nav.nav-right a").Each(func(i int, s *goquery.Selection) {
		hasNextPage = true
	})

	log.Printf("Found %d dealers on listing page", len(dealers))
	return dealers, hasNextPage, nil
}

func saveToCSV(dealers []*Dealer) error {
	now := time.Now()
	timestamp := now.Format("2006-01-02_15-04-05")

	resultsDir := "./results"
	if err := os.MkdirAll(resultsDir, os.ModePerm); err != nil {
		return fmt.Errorf("error creating results directory: %v", err)
	}

	filename := filepath.Join(resultsDir, fmt.Sprintf("dealer_data_%s.csv", timestamp))
	file, err := os.Create(filename)
	if err != nil {
		return fmt.Errorf("error creating CSV file: %v", err)
	}
	defer file.Close()

	writer := csv.NewWriter(file)
	defer writer.Flush()

	headers := []string{
		"URL", "Name", "Location", "Brands", "Ads Count", "Additional Addresses",
	}
	if err := writer.Write(headers); err != nil {
		return fmt.Errorf("error writing CSV header: %v", err)
	}

	for _, dealer := range dealers {
		record := []string{
			dealer.URL, dealer.Name, dealer.Location, dealer.Brands, dealer.AdsCount, dealer.Addresses,
		}
		if err := writer.Write(record); err != nil {
			return fmt.Errorf("error writing CSV record: %v", err)
		}
	}

	fmt.Printf("Data successfully written to %s\n", filename)
	return nil
}

func scrapeAllPages(baseURL string) []*Dealer {
	var allDealers []*Dealer
	pageNum := 1
	for {
		url := fmt.Sprintf("%s%d.html", baseURL, pageNum)
		dealers, hasNextPage, err := scrapeListing(url)
		if err != nil {
			log.Printf("Error scraping page %d: %v", pageNum, err)
			break
		}

		allDealers = append(allDealers, dealers...)

		if !hasNextPage {
			break
		}
		pageNum++
		randomDelay()
	}
	return allDealers
}

func main() {
	baseURL := "https://www.agriaffaires.co.uk/pros/list/"
	dealers := scrapeAllPages(baseURL)
	if err := saveToCSV(dealers); err != nil {
		fmt.Printf("Error saving data to CSV: %v\n", err)
	}
}