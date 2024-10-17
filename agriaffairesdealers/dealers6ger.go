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

type Address struct {
	StreetAddress   string
	PostalCode      string
	AddressLocality string
}

type Dealer struct {
	Name       string
	MainAddress Address
	Addresses  []Address
	PostalCode string
	Activity   string
	Location   string
	AdsCount   string
	Brands     []string
	Website    string
	URL        string
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
		url := fmt.Sprintf("%s/pros/list/%d-germany.html", baseURL, page)
		fmt.Printf("Scraping page %d: %s\n", page, url)

		doc, err := fetchPage(url)
		if err != nil {
			log.Printf("Error fetching page %d: %v", page, err)
			break
		}

		dealerBlocks := doc.Find("div.listing-block.listing-block--dealer")
		if dealerBlocks.Length() == 0 {
			log.Printf("No dealer blocks found on page %d. Stopping.", page)
			break
		}

		dealerBlocks.Each(func(i int, s *goquery.Selection) {
			dealer := scrapeDealerBlock(s, baseURL)
			dealers = append(dealers, dealer)
			fmt.Printf("Scraped: %s (%s)\n", dealer.Name, dealer.URL)
			randomDelay()
		})

		nextPageExists := false
		doc.Find(".pagination--nav.nav-right a").Each(func(i int, s *goquery.Selection) {
			href, exists := s.Attr("href")
			if exists {
				nextPageNumber := page + 1
				expectedHref := fmt.Sprintf("/pros/list/%d-germany.html", nextPageNumber)
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

func scrapeDealerBlock(s *goquery.Selection, baseURL string) Dealer {
	dealer := Dealer{}

	// Extract name and URL
	linkElem := s.Find("a.listing-block__link")
	dealer.Name = strings.TrimSpace(linkElem.Find("span.listing-block__title").Text())
	if href, exists := linkElem.Attr("href"); exists {
		dealer.URL = baseURL + href
	}

	// Extract activity
	dealer.Activity = strings.TrimSpace(s.Find("div.listing-block__activity").Text())

	// Extract location
	dealer.Location = strings.TrimSpace(s.Find("div.listing-block__localisation").Text())

	// Extract brands
	brandsText := s.Find("div.listing-block__brands strong.u-small").Text()
	dealer.Brands = strings.Split(strings.TrimSpace(brandsText), ", ")

	// Extract ads count
	dealer.AdsCount = strings.TrimSpace(s.Find("div.listing-block__number").Text())

	// Scrape additional addresses and main address
	dealer.MainAddress, dealer.Addresses = scrapeAddresses(dealer.URL)

	return dealer
}

func scrapeAddresses(url string) (Address, []Address) {
	doc, err := fetchPage(url)
	if err != nil {
		log.Printf("Error fetching dealer page %s: %v", url, err)
		return Address{}, nil
	}

	mainAddress := Address{}
	addressElem := doc.Find("p[itemprop='address']")
	mainAddress.StreetAddress = strings.TrimSpace(addressElem.Find("span[itemprop='streetAddress']").Text())
	mainAddress.PostalCode = strings.TrimSpace(addressElem.Find("span[itemprop='postalCode']").Text())
	mainAddress.AddressLocality = strings.TrimSpace(addressElem.Find("span[itemprop='addressLocality']").Text())

	var additionalAddresses []Address
	doc.Find("select#js-change-adresse option").Each(func(i int, s *goquery.Selection) {
		addressText := strings.TrimSpace(s.Text())
		if addressText != "" && addressText != "All addresses" {
			parts := strings.SplitN(addressText, " ", 2)
			if len(parts) == 2 {
				additionalAddresses = append(additionalAddresses, Address{
					PostalCode:      parts[0],
					AddressLocality: parts[1],
				})
			}
		}
	})

	return mainAddress, additionalAddresses
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

	headers := []string{"Name", "URL", "Activity", "Location", "Brands", "Ads Count", "Main Street Address", "Main Postal Code", "Main Address Locality", "Additional Addresses"}
	if err := writer.Write(headers); err != nil {
		log.Fatalf("Error writing CSV headers: %v", err)
	}

	for _, dealer := range dealers {
		additionalAddresses := make([]string, len(dealer.Addresses))
		for i, addr := range dealer.Addresses {
			additionalAddresses[i] = fmt.Sprintf("%s %s", addr.PostalCode, addr.AddressLocality)
		}

		record := []string{
			dealer.Name,
			dealer.URL,
			dealer.Activity,
			dealer.Location,
			strings.Join(dealer.Brands, ", "),
			dealer.AdsCount,
			dealer.MainAddress.StreetAddress,
			dealer.MainAddress.PostalCode,
			dealer.MainAddress.AddressLocality,
			strings.Join(additionalAddresses, "; "),
		}
		if err := writer.Write(record); err != nil {
			log.Printf("Error writing dealer record: %v", err)
		}
	}

	return filename
}