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

const App: React.FC = () => {
  const [games, setGames] = useState<Game[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'date_added' | 'date_modified' | 'hottest'>('hottest');
  const [selectedGame, setSelectedGame] = useState<Game | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [favoriteSearch, setFavoriteSearch] = useState('');
  const [favorites, setFavorites] = useState<Game[]>([]);

  const fetchGames = async () => {
    const res = await axios.get<Game[]>(`${process.env.REACT_APP_API_URL}/api/games`, {
      params: {sort_by: sortBy, search_query: searchTerm || undefined},
    });
    setGames(res.data);
  };

  useEffect(() => {
    fetchGames();
    const fav = localStorage.getItem('favoriteGames');
    if (fav) setFavorites(JSON.parse(fav));
  }, [sortBy]);

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
      <div style={{backgroundColor: '#557', width: '100%', height: '100vh'}}>
        <TopAppBar
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          onSearch={fetchGames}
          onSortChange={() =>
            setSortBy((prev) =>
              prev === 'date_added'
                ? 'date_modified'
                : prev === 'date_modified'
                  ? 'hottest'
                  : 'date_added'
            )
          }
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
            <GameGrid games={games} onGameClick={setSelectedGame} onFavorite={handleFavorite} />
          )}
        </Container>
      </ div>
    </ThemeProvider>
  );
};

export default App;
