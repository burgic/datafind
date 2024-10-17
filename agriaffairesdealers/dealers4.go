package main

import (
	"crypto/tls"
	"encoding/csv"
	"fmt"
	"log"
	"math/rand"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/PuerkitoBio/goquery"
)

var rng = rand.New(rand.NewSource(time.Now().UnixNano()))

type Dealer struct {
	Name       string
	Address    string
	PostalCode string
	Locality   string
	Brands     []string
	Website    string
}

func main() {
	dealers := scrapeAllDealers()
	filename := saveToCSV(dealers)
	fmt.Printf("Scraped %d dealers and saved to %s\n", len(dealers), filename)
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

func scrapeAllDealers() []Dealer {
	baseURL := "https://www.agriaffaires.co.uk"
	var dealers []Dealer
	page := 1

	for {
		url := fmt.Sprintf("%s/pros/list/%d-france.html", baseURL, page)
		fmt.Printf("Scraping page %d: %s\n", page, url)
		
		doc, err := fetchPage(url)
		if err != nil {
			log.Printf("Error fetching page %d: %v", page, err)
			break
		}

		dealerLinks := doc.Find("a.listing-block__link")
		if dealerLinks.Length() == 0 {
			log.Printf("No dealer links found on page %d. Stopping.", page)
			break
		}

		dealerLinks.Each(func(i int, s *goquery.Selection) {
			href, exists := s.Attr("href")
			if !exists {
				return
			}
			dealerURL := baseURL + href
			dealer, err := scrapeDealerPage(dealerURL)
			if err != nil {
				log.Printf("Error scraping dealer page %s: %v", dealerURL, err)
				return
			}
			dealers = append(dealers, dealer)
			fmt.Printf("Scraped: %s\n", dealer.Name)
			randomDelay()
		})

		// Check if there's a next page
		nextPageExists := false
		doc.Find(".pagination--nav.nav-right a").Each(func(i int, s *goquery.Selection) {
			href, exists := s.Attr("href")
			if exists {
				nextPageNumber := page + 1
				expectedHref := fmt.Sprintf("/pros/list/%d-france.html", nextPageNumber)
				if href == expectedHref {
					nextPageExists = true
				}
			}
		})

		if !nextPageExists {
			log.Printf("No next page found after page %d. Stopping.", page)
			break
		}

		page++
		randomDelay()
	}

	return dealers
}

func scrapeDealerPage(url string) (Dealer, error) {
	doc, err := fetchPage(url)
	if err != nil {
		return Dealer{}, err
	}

	dealer := Dealer{}

	dealerInfo := doc.Find("div.dealer--fixed")
	dealer.Name = dealerInfo.Find("p.u-bold").Text()
	dealer.Address = dealerInfo.Find("span[data-info='streetAddress']").Text()
	dealer.PostalCode = dealerInfo.Find("span[data-info='postalCode']").Text()
	dealer.Locality = dealerInfo.Find("span[data-info='addressLocality']").Text()

	// Extract makes
	doc.Find("a.tag.no-under.mbs").Each(func(i int, s *goquery.Selection) {
		brand := strings.TrimSpace(s.Text())
		if brand != "" {
			dealer.Brands = append(dealer.Brands, brand)
		}
	})

	// Extract website
	doc.Find("tr").Each(func(i int, s *goquery.Selection) {
		if s.Find("td strong").First().Text() == "Web site" {
			dealer.Website = s.Next().Find("a").Text()
		}
	})

	dealer.Name = strings.TrimSpace(dealer.Name)
	dealer.Address = strings.TrimSpace(dealer.Address)
	dealer.PostalCode = strings.TrimSpace(dealer.PostalCode)
	dealer.Locality = strings.TrimSpace(dealer.Locality)
	dealer.Website = strings.TrimSpace(dealer.Website)

	return dealer, nil
}

func fetchPage(url string) (*goquery.Document, error) {
	resp, err := makeRequest(url)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return nil, fmt.Errorf("status code error: %d %s", resp.StatusCode, resp.Status)
	}

	return goquery.NewDocumentFromReader(resp.Body)
}

func saveToCSV(dealers []Dealer) string {
	timestamp := time.Now().Format("2006-01-02_15-04-05")
	filename := filepath.Join("results", fmt.Sprintf("dealers_%s.csv", timestamp))

	// Ensure the results directory exists
	if err := os.MkdirAll("results", os.ModePerm); err != nil {
		log.Fatalf("Failed to create results directory: %v", err)
	}

	file, err := os.Create(filename)
	if err != nil {
		log.Fatalf("Failed to create file: %v", err)
	}
	defer file.Close()

	writer := csv.NewWriter(file)
	defer writer.Flush()

	headers := []string{"Name", "Address", "Postal Code", "Locality", "Brands", "Website"}
	if err := writer.Write(headers); err != nil {
		log.Fatalf("Error writing CSV headers: %v", err)
	}

	for _, dealer := range dealers {
		record := []string{
			dealer.Name,
			dealer.Address,
			dealer.PostalCode,
			dealer.Locality,
			strings.Join(dealer.Brands, ", "),
			dealer.Website,
		}
		if err := writer.Write(record); err != nil {
			log.Printf("Error writing dealer record: %v", err)
		}
	}

	return filename
}
