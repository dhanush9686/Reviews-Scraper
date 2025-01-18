import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css'; // Import CSS file

const App = () => {
  const [reviews, setReviews] = useState([]);
  const [reviewsCount, setReviewsCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [url, setUrl] = useState('');

  useEffect(() => {
    if (url) {
      fetchReviews(url);
    }
  }, [url]);

  const fetchReviews = async (pageUrl) => {
    setLoading(true);
    try {
      const response = await axios.get(`http://127.0.0.1:5000/api/reviews?page=${pageUrl}`);
      console.log('API Response:', response.data);

      const data = response.data;
      if (data.reviews) {
        setReviews(data.reviews);
        setReviewsCount(data.reviews_count);
      } else {
        setError('No reviews found');
      }
    } catch (err) {
      setError('Failed to fetch reviews');
      console.error('Error fetching reviews:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUrlChange = (e) => {
    setUrl(e.target.value);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (url) {
      fetchReviews(url);
    }
  };

  return (
    <div className="app">
      <h1 className="title">Product Reviews</h1>
      
      <form onSubmit={handleSubmit} className="form">
        <input
          type="text"
          placeholder="Enter product page URL"
          value={url}
          onChange={handleUrlChange}
          className="url-input"
        />
        <button type="submit" className="submit-btn">Fetch Reviews</button>
      </form>

      {loading && <p className="loading">Loading...</p>}
      {error && <p className="error">{error}</p>}

      {reviewsCount > 0 && (
        <div className="reviews-container">
          <p className="review-count">Total Reviews: {reviewsCount}</p>
          <div className="reviews">
            {reviews.map((review, index) => (
              <div key={index} className="review-card">
                <h3 className="review-title">{review.title || 'No title'}</h3>
                <p className="review-rating"><strong>Rating:</strong> {review.rating}</p>
                <p className="reviewer"><strong>Reviewer:</strong> {review.reviewer}</p>
                <p className="review-body">{review.body}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="json-container">
        <h2>Raw Reviews Data (JSON)</h2>
        <pre className="json-data">{JSON.stringify(reviews, null, 2)}</pre>
      </div>
    </div>
  );
};

export default App;
