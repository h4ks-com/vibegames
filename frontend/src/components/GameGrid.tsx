import Grid from '@mui/material/Grid';
import React, { useEffect, useRef } from 'react';
import { Game } from '../types/game';
import { GameCard } from './GameCard';

type Props = {
  games: Game[];
  onGameClick: (game: Game) => void;
  favoriteGames: Game[];
  onFavorite: (game: Game) => void;
  onBottomReached: () => void;
  hasMore: boolean;
};

export const GameGrid: React.FC<Props> = ({ games, onGameClick, favoriteGames, onFavorite, onBottomReached, hasMore }) => {
  const sentinelRef = useRef<HTMLDivElement | null>(null);
  const cardRefs = useRef<(HTMLDivElement | null)[]>([]);

  // Set up an IntersectionObserver to load more pages when the sentinel enters view
  useEffect(() => {
    if (!hasMore) return;
    if (sentinelRef.current === null) return;

    const options = {
      root: null,
      rootMargin: '0px',
      threshold: 0.5,
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        observer.unobserve(entry.target);
        onBottomReached();
      });
    }, options);

    // Observe the last card element
    const lastCard = cardRefs.current[games.length - 1];
    if (lastCard) {
      observer.observe(lastCard);
    }

    // Cleanup on unmount or dependency change
    return () => observer.disconnect();
  }, [hasMore, games, onBottomReached]);

  if (games.length === 0) {
    return (
      <Grid container spacing={2} justifyContent="center">
        <h2>Nothing found</h2>
      </Grid>
    );
  }

  return (
    <>
      <Grid container spacing={2} ref={sentinelRef}>
        {games.map((game, index) => (
          <Grid size={{ xs: 12, sm: 6, md: 4 }} key={game.project}>
            <GameCard
              game={game}
              isFavorite={favoriteGames.some((g) => g.project === game.project)}
              onGameClick={onGameClick}
              onFavorite={() => onFavorite(game)}
              ref={el => {
                cardRefs.current[index] = el;
              }}
            />
          </Grid>
        ))}
      </Grid>
      {hasMore && <div style={{ textAlign: 'center', padding: '1rem' }}>Loading...</div>}
    </>
  );
};
