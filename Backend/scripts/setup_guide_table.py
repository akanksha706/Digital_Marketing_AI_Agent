import asyncio
import asyncpg

async def setup():
    conn = await asyncpg.connect('postgresql://postgres:42works123@localhost:5434/poster_studio')
    
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS studio_guides (
            id SERIAL PRIMARY KEY,
            step_number INT NOT NULL UNIQUE,
            title VARCHAR(200) NOT NULL,
            badge VARCHAR(100) NOT NULL DEFAULT 'Core Workflow',
            short_description TEXT NOT NULL,
            detailed_instructions TEXT NOT NULL,
            icon VARCHAR(50) NOT NULL DEFAULT 'Sparkles',
            feature_highlight VARCHAR(200),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    ''')
    
    await conn.execute('DELETE FROM studio_guides')
    
    steps = [
        (
            1,
            'Creative Prompting & Cultural Themes',
            'Step 1 • Studio Generator',
            'Describe your marketing narrative or click ready-made festival themes like Chatth Puja, Diwali, or AI Innovation.',
            '1. In the Studio Generator, type a detailed description (e.g., celebration vibe, colors, audience).\n2. Select your channel aspect ratio: 1:1 Square (Instagram/LinkedIn), 4:5 Portrait, or 16:9 Landscape.\n3. Or click any Inspiration Chip or Showcase Theme to auto-populate a proven agency prompt.\n4. Press Ctrl+Enter or click "Generate Poster".',
            'Sparkles',
            'Aspect ratio auto-formatting & cultural prompts'
        ),
        (
            2,
            'Multi-Stage Neural AI Pipeline',
            'Step 2 • Generation Engine',
            'Witness the 3-stage neural pipeline: copywriting, high-res visual diffusion, and typography compositing.',
            'Stage 1: Synthesizes cultural hooks, golden quotes, catchy headline, and targeted hashtags.\nStage 2: Diffuses a photorealistic, cinematic image backdrop using generative AI.\nStage 3: Composites golden-ratio typography, brand logos, and contrast scrims in high resolution.',
            'Cpu',
            'Real-time staged progress loader'
        ),
        (
            3,
            '3D Appreciative Review & In-Place Editing',
            'Step 3 • Creative Review',
            'Experience 3D perspective tilt, holographic light glare, and instant text editing without waiting.',
            '1. Hover over the poster to feel the 3D gyro tilt and light reflection.\n2. Double-click or click ❤️ to send celebratory GSAP particle bursts.\n3. Need to tweak the headline or quote? Edit the text fields in the review modal and click "Re-composite" — it updates in under 20ms without re-generating the image!',
            'Eye',
            'Instant <20ms typography recomposition'
        ),
        (
            4,
            'Social Dispatch & Scheduling',
            'Step 4 • Multi-Channel Delivery',
            'Publish immediately to LinkedIn & Instagram or schedule for prime audience engagement times.',
            '1. Choose your platform: LinkedIn Company Page or Instagram Business Feed.\n2. Click "Publish Now" to dispatch immediately.\n3. Or click "Schedule Send" to choose an upcoming date and time.\nNote: In development without API keys, dispatch is safely simulated and logged in PostgreSQL. Once real API keys are entered in .env, it posts live to real feeds!',
            'Send',
            'Direct API publishing & scheduled worker queue'
        ),
        (
            5,
            'Creator Analytics & Soft Archiving',
            'Step 5 • Admin & Lifecycle',
            'Track publishing performance across creators, and archive cleanups without erasing metrics.',
            '1. The Admin Panel displays weekly, monthly, and yearly publishing counts per creator.\n2. When creators delete old published posters from their library, the system safely "Soft-Archives" them: they disappear from the active workspace, but their live social post stays alive and Admin performance metrics remain 100% accurate!',
            'BarChart3',
            'Safe soft-archiving & creator tracking'
        )
    ]
    
    for s in steps:
        await conn.execute('''
            INSERT INTO studio_guides (
                step_number, title, badge, short_description, detailed_instructions, icon, feature_highlight
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        ''', *s)
        
    count = await conn.fetchval('SELECT COUNT(*) FROM studio_guides')
    print(f'Successfully created and seeded {count} studio guide steps!')
    await conn.close()

if __name__ == '__main__':
    asyncio.run(setup())
