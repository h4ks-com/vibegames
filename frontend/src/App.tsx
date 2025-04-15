// src/App.tsx
import React, {useEffect, useState} from 'react';
import {ThemeProvider, Container} from '@mui/material';
import {Game} from './types/game';
import theme from './theme';
import axios from 'axios';
import {TopAppBar} from './components/AppBar';
import {GameGrid} from './components/GameGrid';
import {GameView} from './components/GameView';
import {Sidebar} from './components/Sidebar';
import {SortByOptions} from './types/api';

const App: React.FC = () => {
  const [games, setGames] = useState<Game[]>([]);
  const [searchTerm, setSearchTerm] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<SortByOptions>('hottest');
  const [selectedGame, setSelectedGame] = useState<Game | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [favoriteSearch, setFavoriteSearch] = useState('');
  const [favorites, setFavorites] = useState<Game[]>([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  const fetchGames = async () => {
    const res = await axios.get<Game[]>(`${process.env.REACT_APP_API_URL}/api/games`, {
      params: {
        sort_by: sortBy,
        search_query: searchTerm || undefined,
        page: page,
      }
    });
    if (page === 1) {
      setGames(res.data);
    } else {
      setGames((prev) => [...prev, ...res.data]);
    }
    if (res.data.length < 20) {
      setHasMore(false);
    }
  };

  useEffect(() => {
    fetchGames();
    const fav = localStorage.getItem('favoriteGames');
    if (fav) setFavorites(JSON.parse(fav));
  }, [sortBy, searchTerm, page]);

  const handleFavorite = (game: Game) => {
    const updated = [...favorites, game];
    setFavorites(updated);
    // Avoid duplicates
    const unique = updated.filter((g, index, self) =>
      index === self.findIndex((t) => t.project === g.project)
    );
    setFavorites(unique);
  };

  return (
    <ThemeProvider theme={theme} >
      <TopAppBar
        onSearch={setSearchTerm}
        onSortChange={setSortBy}
        sortBy={sortBy}
        openDrawer={() => setDrawerOpen(true)}
      />
      <Sidebar
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        favorites={favorites}
        search={favoriteSearch}
        setSearch={setFavoriteSearch}
      />
      <Container sx={{mt: 2}}>
        {selectedGame ? (
          <GameView game={selectedGame} onBack={() => setSelectedGame(null)} />
        ) : (
          <GameGrid
            games={games}
            onGameClick={setSelectedGame}
            onFavorite={handleFavorite}
            hasMore={hasMore}
            onBottomReached={() => setPage((prev) => prev + 1)}
          />
        )}
      </Container>
    </ThemeProvider>
  );
};

export default App;
